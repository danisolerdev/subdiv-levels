"""Operadores del addon Sculpt Subtools (prefijo sculpt_ext.subtool_*)."""

import bmesh
import bpy
from bpy.props import EnumProperty, IntProperty, StringProperty

from . import preview, utils

# Nombres de atributo estándar en Blender 5.x (verificados en spike).
FACE_SET_ATTR = ".sculpt_face_set"
MASK_ATTR = ".sculpt_mask"


def _poll_mesh(context) -> bool:
    """Hay objeto activo, es malla y no está en modo Edit."""
    obj = context.object
    return obj is not None and obj.type == 'MESH' and obj.mode != 'EDIT'


def _multires_of(obj):
    """Primer modificador Multires del objeto, o None."""
    for mod in obj.modifiers:
        if mod.type == 'MULTIRES':
            return mod
    return None


def _object_from_faces(src_obj, keep_indices, name, collection):
    """Crea un objeto nuevo con solo las caras `keep_indices` de `src_obj`."""
    bm = bmesh.new()
    bm.from_mesh(src_obj.data)
    bm.faces.ensure_lookup_table()
    keep = set(keep_indices)
    to_delete = [f for f in bm.faces if f.index not in keep]
    bmesh.ops.delete(bm, geom=to_delete, context='FACES')
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    new_obj = bpy.data.objects.new(name, me)
    new_obj.matrix_world = src_obj.matrix_world.copy()
    collection.objects.link(new_obj)
    return new_obj


def _delete_faces_inplace(obj, face_indices):
    """Borra las caras indicadas del propio datablock de `obj`."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    drop = set(face_indices)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index in drop], context='FACES')
    bm.to_mesh(me)
    bm.free()
    me.update()


def _redraw(context):
    """Fuerza el refresco del área activa."""
    if context.area is not None:
        context.area.tag_redraw()


def _deselect_all(context):
    for o in context.selected_objects:
        o.select_set(False)


def _make_active(context, obj):
    """Deja `obj` como único seleccionado y activo."""
    _deselect_all(context)
    obj.select_set(True)
    context.view_layer.objects.active = obj


# --- Activar / ciclar ---------------------------------------------------------

class SCULPTEXT_OT_subtool_activate(bpy.types.Operator):
    """Hace activo este subtool (salta a él sin salir de Sculpt)"""

    bl_idname = "sculpt_ext.subtool_activate"
    bl_label = "Activar subtool"
    bl_options = {'REGISTER'}

    name: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        obj = bpy.data.objects.get(self.name)
        if obj is None or obj.type != 'MESH':
            self.report({'WARNING'}, "Subtool no encontrado")
            return {'CANCELLED'}
        if obj == context.object and not obj.hide_get():
            return {'CANCELLED'}  # ya es el subtool activo y visible

        prefs = utils.get_prefs()
        was_sculpt = context.mode == 'SCULPT'
        leaving = context.object

        if obj.hide_get():
            obj.hide_set(False)

        # Rebote: para cambiar el objeto que se esculpe hay que salir a Objeto,
        # reasignar el activo y (opcionalmente) reentrar en Sculpt.
        if was_sculpt:
            bpy.ops.object.mode_set(mode='OBJECT')
        # Recapturar la miniatura del subtool que dejamos (ya en modo Objeto).
        if leaving is not None and leaving is not obj and leaving.type == 'MESH':
            preview.maybe_capture(context, leaving)
        _make_active(context, obj)
        if was_sculpt and prefs.switch_reenters_sculpt:
            bpy.ops.object.mode_set(mode='SCULPT')

        _redraw(context)
        return {'FINISHED'}


class SCULPTEXT_OT_subtool_cycle(bpy.types.Operator):
    """Salta al subtool anterior o siguiente del Tool activo"""

    bl_idname = "sculpt_ext.subtool_cycle"
    bl_label = "Ciclar subtool"
    bl_options = {'REGISTER'}

    direction: EnumProperty(
        items=(
            ('PREV', "Anterior", "Subtool anterior"),
            ('NEXT', "Siguiente", "Subtool siguiente"),
        ),
        default='NEXT',
    )

    @classmethod
    def poll(cls, context):
        return _poll_mesh(context)

    def execute(self, context):
        obj = context.object
        prefs = utils.get_prefs()
        root = utils.get_tool_root(obj)
        chain = utils.all_subtools(root, prefs.sort_mode)
        if obj not in chain or len(chain) < 2:
            self.report({'INFO'}, "No hay otro subtool al que saltar")
            return {'CANCELLED'}
        idx = chain.index(obj)
        step = -1 if self.direction == 'PREV' else 1
        target = chain[(idx + step) % len(chain)]
        bpy.ops.sculpt_ext.subtool_activate(name=target.name)
        return {'FINISHED'}


# --- Visibilidad / Solo -------------------------------------------------------

class SCULPTEXT_OT_subtool_toggle_visible(bpy.types.Operator):
    """Muestra u oculta este subtool"""

    bl_idname = "sculpt_ext.subtool_toggle_visible"
    bl_label = "Visibilidad del subtool"
    bl_options = {'REGISTER'}

    name: StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.name)
        if obj is None:
            return {'CANCELLED'}
        obj.hide_set(not obj.hide_get())
        _redraw(context)
        return {'FINISHED'}


class SCULPTEXT_OT_subtool_solo(bpy.types.Operator):
    """Aísla este subtool ocultando el resto (toggle)"""

    bl_idname = "sculpt_ext.subtool_solo"
    bl_label = "Solo"
    bl_options = {'REGISTER'}

    name: StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.name)
        if obj is None:
            return {'CANCELLED'}
        scene = context.scene
        prefs = utils.get_prefs()
        root = utils.get_tool_root(obj)
        subs = utils.all_subtools(root)

        if scene.subtool_solo_active == obj.name:
            # Desactivar Solo: restaurar visibilidad desde el snapshot.
            for o in subs:
                o.hide_set(o.subtool_prev_hidden)
            scene.subtool_solo_active = ""
        else:
            # Activar Solo. Tomar snapshot solo si no había otro Solo activo.
            if scene.subtool_solo_active == "":
                for o in subs:
                    o.subtool_prev_hidden = o.hide_get()
            keep = {obj}
            if prefs.solo_includes_group and obj.users_collection:
                keep.update(utils.all_subtools(obj.users_collection[0]))
            for o in subs:
                o.hide_set(o not in keep)
            scene.subtool_solo_active = obj.name

        _redraw(context)
        return {'FINISHED'}


# --- Duplicar / borrar --------------------------------------------------------

class SCULPTEXT_OT_subtool_duplicate(bpy.types.Operator):
    """Duplica el subtool activo"""

    bl_idname = "sculpt_ext.subtool_duplicate"
    bl_label = "Duplicar subtool"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_mesh(context)

    def execute(self, context):
        obj = context.object
        was_sculpt = context.mode == 'SCULPT'
        if was_sculpt:
            bpy.ops.object.mode_set(mode='OBJECT')

        _make_active(context, obj)
        bpy.ops.object.duplicate()
        dup = context.object  # duplicate deja el nuevo objeto como activo
        dup.subtool_order = obj.subtool_order + 1
        preview.maybe_capture(context, dup)

        if was_sculpt:
            bpy.ops.object.mode_set(mode='SCULPT')
        _redraw(context)
        self.report({'INFO'}, f"Duplicado: {dup.name}")
        return {'FINISHED'}


class SCULPTEXT_OT_subtool_delete(bpy.types.Operator):
    """Borra el subtool activo"""

    bl_idname = "sculpt_ext.subtool_delete"
    bl_label = "Borrar subtool"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_mesh(context)

    def invoke(self, context, event):
        if utils.get_prefs().confirm_delete:
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)

    def execute(self, context):
        obj = context.object
        was_sculpt = context.mode == 'SCULPT'
        root = utils.get_tool_root(obj)
        remaining = [o for o in utils.all_subtools(root) if o != obj]

        if was_sculpt:
            bpy.ops.object.mode_set(mode='OBJECT')

        me = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)

        if remaining:
            _make_active(context, remaining[0])
            if was_sculpt:
                bpy.ops.object.mode_set(mode='SCULPT')
        _redraw(context)
        self.report({'INFO'}, "Subtool borrado")
        return {'FINISHED'}


# --- Orden / grupos -----------------------------------------------------------

class SCULPTEXT_OT_subtool_move(bpy.types.Operator):
    """Sube o baja el subtool activo en su grupo"""

    bl_idname = "sculpt_ext.subtool_move"
    bl_label = "Mover subtool"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        items=(
            ('UP', "Subir", "Mover arriba"),
            ('DOWN', "Bajar", "Mover abajo"),
        ),
        default='UP',
    )

    @classmethod
    def poll(cls, context):
        return _poll_mesh(context)

    def execute(self, context):
        obj = context.object
        if not obj.users_collection:
            return {'CANCELLED'}
        coll = obj.users_collection[0]
        siblings = utils.subtools_of(coll, 'MANUAL')
        # Normalizar el orden para garantizar valores distintos antes de intercambiar.
        for i, o in enumerate(siblings):
            o.subtool_order = i
        idx = siblings.index(obj)
        swap = idx - 1 if self.direction == 'UP' else idx + 1
        if swap < 0 or swap >= len(siblings):
            self.report({'INFO'}, "El subtool ya está en el extremo")
            return {'CANCELLED'}
        other = siblings[swap]
        obj.subtool_order, other.subtool_order = other.subtool_order, obj.subtool_order
        _redraw(context)
        return {'FINISHED'}


class SCULPTEXT_OT_subtool_group_new(bpy.types.Operator):
    """Crea un grupo (sub-colección) dentro del Tool activo"""

    bl_idname = "sculpt_ext.subtool_group_new"
    bl_label = "Nuevo grupo"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(name="Nombre", default="Grupo")

    @classmethod
    def poll(cls, context):
        return _poll_mesh(context)

    def execute(self, context):
        root = utils.get_tool_root(context.object)
        group = bpy.data.collections.new(self.name)
        root.children.link(group)
        _redraw(context)
        self.report({'INFO'}, f"Grupo creado: {group.name}")
        return {'FINISHED'}


class SCULPTEXT_OT_subtool_move_to_group(bpy.types.Operator):
    """Mueve el subtool activo al grupo indicado"""

    bl_idname = "sculpt_ext.subtool_move_to_group"
    bl_label = "Mover a grupo"
    bl_options = {'REGISTER', 'UNDO'}

    group: StringProperty()

    @classmethod
    def poll(cls, context):
        return _poll_mesh(context)

    def execute(self, context):
        obj = context.object
        target = bpy.data.collections.get(self.group)
        if target is None:
            self.report({'WARNING'}, "Grupo no encontrado")
            return {'CANCELLED'}
        if obj.name in target.objects:
            return {'CANCELLED'}
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        target.objects.link(obj)
        _redraw(context)
        self.report({'INFO'}, f"Movido a {target.name}")
        return {'FINISHED'}


class SCULPTEXT_OT_subtool_toggle_expand(bpy.types.Operator):
    """Pliega o despliega un grupo en la paleta"""

    bl_idname = "sculpt_ext.subtool_toggle_expand"
    bl_label = "Plegar/desplegar grupo"
    bl_options = {'REGISTER'}

    collection: StringProperty()

    def execute(self, context):
        coll = bpy.data.collections.get(self.collection)
        if coll is None:
            return {'CANCELLED'}
        coll.subtool_expanded = not coll.subtool_expanded
        _redraw(context)
        return {'FINISHED'}


# --- Merge / split ------------------------------------------------------------

class SCULPTEXT_OT_subtool_merge(bpy.types.Operator):
    """Une los subtools seleccionados en el activo"""

    bl_idname = "sculpt_ext.subtool_merge"
    bl_label = "Unir subtools"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not _poll_mesh(context):
            return False
        meshes = [o for o in context.selected_objects if o.type == 'MESH']
        return len(meshes) >= 2

    def invoke(self, context, event):
        if utils.get_prefs().confirm_merge:
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)

    def execute(self, context):
        active = context.object
        selected = [o for o in context.selected_objects if o.type == 'MESH']
        has_multires = any(
            any(m.type == 'MULTIRES' for m in o.modifiers) for o in selected
        )
        was_sculpt = context.mode == 'SCULPT'
        if was_sculpt:
            bpy.ops.object.mode_set(mode='OBJECT')

        context.view_layer.objects.active = active
        result = bpy.ops.object.join()

        if was_sculpt:
            bpy.ops.object.mode_set(mode='SCULPT')
        if 'FINISHED' not in result:
            self.report({'WARNING'}, "No se pudieron unir los subtools")
            return {'CANCELLED'}
        _redraw(context)
        if has_multires:
            self.report({'WARNING'},
                        "Subtools unidos; el Multires no se conserva al unir")
        else:
            self.report({'INFO'}, "Subtools unidos")
        return {'FINISHED'}


class SCULPTEXT_OT_subtool_split_loose(bpy.types.Operator):
    """Separa el subtool activo en sus partes sueltas"""

    bl_idname = "sculpt_ext.subtool_split_loose"
    bl_label = "Separar por partes sueltas"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_mesh(context)

    def execute(self, context):
        obj = context.object
        was_sculpt = context.mode == 'SCULPT'
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        _make_active(context, obj)
        before = set(bpy.data.objects)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.separate(type='LOOSE')
        bpy.ops.object.mode_set(mode='OBJECT')
        new_objs = [o for o in bpy.data.objects if o not in before]
        preview.maybe_capture_many(context, new_objs + [obj])

        if was_sculpt:
            _make_active(context, obj)
            bpy.ops.object.mode_set(mode='SCULPT')
        _redraw(context)
        if new_objs:
            self.report({'INFO'}, f"Separado en {len(new_objs) + 1} subtools")
        else:
            self.report({'INFO'}, "El subtool no tiene partes sueltas")
        return {'FINISHED'}


# --- Crear / espejar ----------------------------------------------------------

class SCULPTEXT_OT_subtool_add(bpy.types.Operator):
    """Añade una malla primitiva nueva como subtool del Tool activo"""

    bl_idname = "sculpt_ext.subtool_add"
    bl_label = "Añadir subtool"
    bl_options = {'REGISTER', 'UNDO'}

    kind: EnumProperty(
        items=(
            ('CUBE', "Cubo", "Añadir un cubo"),
            ('SPHERE', "Esfera", "Añadir una esfera"),
            ('CYLINDER', "Cilindro", "Añadir un cilindro"),
            ('PLANE', "Plano", "Añadir un plano"),
        ),
        default='CUBE',
    )

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT', 'SCULPT'}

    def execute(self, context):
        active = context.object
        if active is not None and active.users_collection:
            coll = active.users_collection[0]
        else:
            coll = context.scene.collection

        was_sculpt = context.mode == 'SCULPT'
        if was_sculpt:
            bpy.ops.object.mode_set(mode='OBJECT')

        adders = {
            'CUBE': bpy.ops.mesh.primitive_cube_add,
            'SPHERE': bpy.ops.mesh.primitive_uv_sphere_add,
            'CYLINDER': bpy.ops.mesh.primitive_cylinder_add,
            'PLANE': bpy.ops.mesh.primitive_plane_add,
        }
        adders[self.kind]()
        new_obj = context.active_object

        # Reubicar el objeto nuevo en la colección del Tool.
        for c in list(new_obj.users_collection):
            if c != coll:
                c.objects.unlink(new_obj)
        if new_obj.name not in coll.objects:
            coll.objects.link(new_obj)
        preview.maybe_capture(context, new_obj)

        if was_sculpt:
            bpy.ops.object.mode_set(mode='SCULPT')
        _redraw(context)
        self.report({'INFO'}, f"Subtool añadido: {new_obj.name}")
        return {'FINISHED'}


class SCULPTEXT_OT_subtool_mirror(bpy.types.Operator):
    """Crea una copia reflejada del subtool activo sobre un eje"""

    bl_idname = "sculpt_ext.subtool_mirror"
    bl_label = "Espejar subtool"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        items=(
            ('X', "X", "Reflejar en el eje X"),
            ('Y', "Y", "Reflejar en el eje Y"),
            ('Z', "Z", "Reflejar en el eje Z"),
        ),
        default='X',
    )

    @classmethod
    def poll(cls, context):
        return _poll_mesh(context)

    def execute(self, context):
        obj = context.object
        was_sculpt = context.mode == 'SCULPT'
        if was_sculpt:
            bpy.ops.object.mode_set(mode='OBJECT')

        _make_active(context, obj)
        bpy.ops.object.duplicate()
        dup = context.object
        index = {'X': 0, 'Y': 1, 'Z': 2}[self.axis]
        dup.scale[index] *= -1.0
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        # La escala negativa invierte las normales: recomponerlas.
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.flip_normals()
        bpy.ops.object.mode_set(mode='OBJECT')
        dup.subtool_order = obj.subtool_order + 1
        preview.maybe_capture(context, dup)

        if was_sculpt:
            bpy.ops.object.mode_set(mode='SCULPT')
        _redraw(context)
        self.report({'INFO'}, f"Espejo creado: {dup.name}")
        return {'FINISHED'}


# --- Acciones globales --------------------------------------------------------

class SCULPTEXT_OT_subtool_show_all(bpy.types.Operator):
    """Muestra todos los subtools del Tool y desactiva el Solo"""

    bl_idname = "sculpt_ext.subtool_show_all"
    bl_label = "Mostrar todos"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return _poll_mesh(context)

    def execute(self, context):
        root = utils.get_tool_root(context.object)
        for o in utils.all_subtools(root):
            o.hide_set(False)
        context.scene.subtool_solo_active = ""
        _redraw(context)
        return {'FINISHED'}


class SCULPTEXT_OT_subtool_frame_active(bpy.types.Operator):
    """Encuadra la vista sobre el subtool activo"""

    bl_idname = "sculpt_ext.subtool_frame_active"
    bl_label = "Enmarcar activo"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        try:
            bpy.ops.view3d.view_selected('INVOKE_DEFAULT')
        except RuntimeError as error:
            self.report({'WARNING'}, f"No se pudo encuadrar: {error}")
            return {'CANCELLED'}
        return {'FINISHED'}


# --- Splits avanzados (bmesh sobre atributos) ---------------------------------

class SCULPTEXT_OT_subtool_split_faceset(bpy.types.Operator):
    """Separa el subtool activo en un subtool por cada Face Set"""

    bl_idname = "sculpt_ext.subtool_split_faceset"
    bl_label = "Separar por Face Sets"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_mesh(context)

    def execute(self, context):
        obj = context.object
        me = obj.data
        attr = me.attributes.get(FACE_SET_ATTR)
        if attr is None:
            self.report({'WARNING'}, "La malla no tiene Face Sets")
            return {'CANCELLED'}

        groups = {}
        for i in range(len(me.polygons)):
            groups.setdefault(attr.data[i].value, []).append(i)
        if len(groups) < 2:
            self.report({'INFO'}, "Solo hay un Face Set: nada que separar")
            return {'CANCELLED'}

        was_sculpt = context.mode == 'SCULPT'
        if was_sculpt:
            bpy.ops.object.mode_set(mode='OBJECT')

        coll = obj.users_collection[0] if obj.users_collection else context.scene.collection
        base_name = obj.name
        base_order = obj.subtool_order
        new_objs = []
        for offset, (value, faces) in enumerate(sorted(groups.items())):
            piece = _object_from_faces(obj, faces, f"{base_name}_fs{value}", coll)
            piece.subtool_order = base_order + offset
            new_objs.append(piece)

        # Sustituir el original por las piezas.
        old_mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if old_mesh is not None and old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)

        preview.maybe_capture_many(context, new_objs)
        _make_active(context, new_objs[0])
        if was_sculpt:
            bpy.ops.object.mode_set(mode='SCULPT')
        _redraw(context)
        self.report({'INFO'}, f"Separado en {len(new_objs)} subtools por Face Set")
        return {'FINISHED'}


class SCULPTEXT_OT_subtool_split_mask(bpy.types.Operator):
    """Separa la zona enmascarada del subtool activo a un subtool nuevo"""

    bl_idname = "sculpt_ext.subtool_split_mask"
    bl_label = "Separar por máscara"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_mesh(context)

    def execute(self, context):
        obj = context.object
        me = obj.data
        attr = me.attributes.get(MASK_ATTR)
        if attr is None:
            self.report({'WARNING'}, "La malla no tiene máscara de Sculpt")
            return {'CANCELLED'}

        mask = [attr.data[i].value for i in range(len(me.vertices))]
        masked_faces = []
        for poly in me.polygons:
            verts = poly.vertices
            avg = sum(mask[v] for v in verts) / len(verts)
            if avg >= 0.5:
                masked_faces.append(poly.index)

        if not masked_faces:
            self.report({'INFO'}, "No hay zona enmascarada")
            return {'CANCELLED'}
        if len(masked_faces) == len(me.polygons):
            self.report({'INFO'}, "Toda la malla está enmascarada: nada que separar")
            return {'CANCELLED'}

        was_sculpt = context.mode == 'SCULPT'
        if was_sculpt:
            bpy.ops.object.mode_set(mode='OBJECT')

        coll = obj.users_collection[0] if obj.users_collection else context.scene.collection
        piece = _object_from_faces(obj, masked_faces, f"{obj.name}_mask", coll)
        piece.subtool_order = obj.subtool_order + 1
        _delete_faces_inplace(obj, masked_faces)
        preview.maybe_capture_many(context, [piece, obj])

        _make_active(context, piece)
        if was_sculpt:
            bpy.ops.object.mode_set(mode='SCULPT')
        _redraw(context)
        self.report({'INFO'}, "Zona enmascarada separada a un subtool nuevo")
        return {'FINISHED'}


# --- Integración con Multires / Subdiv Levels ---------------------------------

class SCULPTEXT_OT_subtool_multires_step(bpy.types.Operator):
    """Sube o baja el nivel de Multires del subtool activo"""

    bl_idname = "sculpt_ext.subtool_multires_step"
    bl_label = "Nivel Multires"
    bl_options = {'REGISTER', 'UNDO'}

    delta: IntProperty(default=1)

    @classmethod
    def poll(cls, context):
        return _poll_mesh(context) and _multires_of(context.object) is not None

    def execute(self, context):
        obj = context.object
        mod = _multires_of(obj)
        level = max(0, min(mod.sculpt_levels + self.delta, mod.total_levels))
        mod.sculpt_levels = level
        mod.levels = level
        obj.update_tag()
        _redraw(context)
        return {'FINISHED'}


# --- Booleanas ----------------------------------------------------------------

_BOOL_OPS = ('NONE', 'ADD', 'SUBTRACT', 'INTERSECT')
_BOOL_OP_TO_MOD = {'ADD': 'UNION', 'SUBTRACT': 'DIFFERENCE', 'INTERSECT': 'INTERSECT'}
# Orden de aplicación: primero unir (sembrar volumen), luego intersecar, luego restar.
_BOOL_ORDER = {'ADD': 0, 'INTERSECT': 1, 'SUBTRACT': 2}


def _bool_operands(root):
    """Subtools con rol booleano (excluye el objeto de resultado), en orden de aplicación."""
    ops = [o for o in utils.all_subtools(root)
           if not o.subtool_is_bool_result and o.subtool_bool_op != 'NONE']
    return sorted(ops, key=lambda o: (_BOOL_ORDER[o.subtool_bool_op], o.subtool_order))


def _build_bool_result(root, operands):
    """Crea el objeto de resultado con un modificador Boolean por operando."""
    me = bpy.data.meshes.new(f"{root.name}_bool")
    res = bpy.data.objects.new(f"{root.name}_bool", me)
    res.subtool_is_bool_result = True
    root.objects.link(res)
    for operand in operands:
        mod = res.modifiers.new(name=f"bool_{operand.name}", type='BOOLEAN')
        mod.operation = _BOOL_OP_TO_MOD[operand.subtool_bool_op]
        mod.object = operand
        mod.solver = 'EXACT'
    return res


def _remove_object(obj):
    if obj is None:
        return
    me = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if me is not None and me.users == 0:
        bpy.data.meshes.remove(me)


class SCULPTEXT_OT_subtool_bool_cycle_op(bpy.types.Operator):
    """Cambia el rol booleano del subtool: Ninguno → Añadir → Restar → Intersecar"""

    bl_idname = "sculpt_ext.subtool_bool_cycle_op"
    bl_label = "Rol booleano"
    bl_options = {'REGISTER', 'UNDO'}

    target: StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.target)
        if obj is None:
            return {'CANCELLED'}
        idx = _BOOL_OPS.index(obj.subtool_bool_op)
        obj.subtool_bool_op = _BOOL_OPS[(idx + 1) % len(_BOOL_OPS)]
        _redraw(context)
        return {'FINISHED'}


class SCULPTEXT_OT_subtool_bool_preview(bpy.types.Operator):
    """Activa/desactiva el preview en vivo de la booleana del Tool"""

    bl_idname = "sculpt_ext.subtool_bool_preview"
    bl_label = "Preview booleano en vivo"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return _poll_mesh(context)

    def execute(self, context):
        scene = context.scene
        root = utils.get_tool_root(context.object)

        if scene.subtool_bool_active:
            # Desactivar: eliminar el resultado y mostrar los operandos.
            _remove_object(bpy.data.objects.get(scene.subtool_bool_active))
            scene.subtool_bool_active = ""
            for o in utils.all_subtools(root):
                if not o.subtool_is_bool_result:
                    o.hide_set(False)
            _redraw(context)
            return {'FINISHED'}

        operands = _bool_operands(root)
        if not any(o.subtool_bool_op == 'ADD' for o in operands):
            self.report({'WARNING'}, "Marca al menos un subtool como 'Añadir'")
            return {'CANCELLED'}

        was_sculpt = context.mode == 'SCULPT'
        if was_sculpt:
            bpy.ops.object.mode_set(mode='OBJECT')

        res = _build_bool_result(root, operands)
        for o in operands:
            o.hide_set(True)
        scene.subtool_bool_active = res.name
        _make_active(context, res)

        if was_sculpt:
            bpy.ops.object.mode_set(mode='SCULPT')
        _redraw(context)
        self.report({'INFO'}, f"Preview booleano: {len(operands)} operandos")
        return {'FINISHED'}


class SCULPTEXT_OT_subtool_bool_apply(bpy.types.Operator):
    """Hornea la booleana: aplica el resultado y elimina los operandos"""

    bl_idname = "sculpt_ext.subtool_bool_apply"
    bl_label = "Aplicar booleana"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_mesh(context)

    def execute(self, context):
        scene = context.scene
        root = utils.get_tool_root(context.object)
        operands = _bool_operands(root)
        if not any(o.subtool_bool_op == 'ADD' for o in operands):
            self.report({'WARNING'}, "Marca al menos un subtool como 'Añadir'")
            return {'CANCELLED'}

        was_sculpt = context.mode == 'SCULPT'
        if was_sculpt:
            bpy.ops.object.mode_set(mode='OBJECT')

        # Reutilizar el resultado del preview si existe; si no, construir uno.
        res = bpy.data.objects.get(scene.subtool_bool_active) if scene.subtool_bool_active else None
        if res is None:
            res = _build_bool_result(root, operands)
        scene.subtool_bool_active = ""

        _make_active(context, res)
        for mod_name in [m.name for m in res.modifiers]:
            try:
                bpy.ops.object.modifier_apply(modifier=mod_name)
            except RuntimeError as error:
                self.report({'WARNING'}, f"No se pudo aplicar {mod_name}: {error}")

        res.subtool_is_bool_result = False
        res.subtool_bool_op = 'NONE'
        for operand in operands:
            _remove_object(operand)

        _make_active(context, res)
        if was_sculpt:
            bpy.ops.object.mode_set(mode='SCULPT')
        _redraw(context)
        self.report({'INFO'}, "Booleana aplicada")
        return {'FINISHED'}


class SCULPTEXT_OT_subtool_bool_direct(bpy.types.Operator):
    """Booleana directa: aplica al subtool activo el resto de seleccionados y los borra"""

    bl_idname = "sculpt_ext.subtool_bool_direct"
    bl_label = "Booleana directa"
    bl_options = {'REGISTER', 'UNDO'}

    op: EnumProperty(
        items=(
            ('UNION', "Unión", "Unir al activo"),
            ('DIFFERENCE', "Resta", "Restar del activo"),
            ('INTERSECT', "Intersección", "Dejar el volumen común"),
        ),
        default='DIFFERENCE',
    )

    @classmethod
    def poll(cls, context):
        if not _poll_mesh(context):
            return False
        meshes = [o for o in context.selected_objects if o.type == 'MESH']
        return len(meshes) >= 2

    def execute(self, context):
        active = context.object
        others = [o for o in context.selected_objects
                  if o.type == 'MESH' and o != active]
        if not others:
            self.report({'WARNING'}, "Selecciona el activo y al menos otro subtool")
            return {'CANCELLED'}

        was_sculpt = context.mode == 'SCULPT'
        if was_sculpt:
            bpy.ops.object.mode_set(mode='OBJECT')

        context.view_layer.objects.active = active
        added = []
        for operand in others:
            mod = active.modifiers.new(name="bool_direct", type='BOOLEAN')
            mod.operation = self.op
            mod.object = operand
            mod.solver = 'EXACT'
            added.append(mod.name)

        failed = False
        for mod_name in added:
            try:
                bpy.ops.object.modifier_apply(modifier=mod_name)
            except RuntimeError:
                failed = True

        for operand in others:
            _remove_object(operand)

        if was_sculpt:
            bpy.ops.object.mode_set(mode='SCULPT')
        _redraw(context)
        if failed:
            self.report({'WARNING'},
                        "Alguna booleana no se aplicó (¿Multires en la pila del activo?)")
        else:
            self.report({'INFO'}, f"Booleana {self.op} aplicada")
        return {'FINISHED'}


class SCULPTEXT_OT_subtool_rename(bpy.types.Operator):
    """Renombra este subtool"""

    bl_idname = "sculpt_ext.subtool_rename"
    bl_label = "Renombrar subtool"
    bl_options = {'REGISTER', 'UNDO'}

    target: StringProperty()
    new_name: StringProperty(name="Nombre")

    def invoke(self, context, event):
        obj = bpy.data.objects.get(self.target)
        if obj is None:
            return {'CANCELLED'}
        self.new_name = obj.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "new_name")

    def execute(self, context):
        obj = bpy.data.objects.get(self.target)
        if obj is None:
            self.report({'WARNING'}, "Subtool no encontrado")
            return {'CANCELLED'}
        if self.new_name:
            obj.name = self.new_name
        _redraw(context)
        return {'FINISHED'}


classes = (
    SCULPTEXT_OT_subtool_activate,
    SCULPTEXT_OT_subtool_rename,
    SCULPTEXT_OT_subtool_cycle,
    SCULPTEXT_OT_subtool_toggle_visible,
    SCULPTEXT_OT_subtool_solo,
    SCULPTEXT_OT_subtool_duplicate,
    SCULPTEXT_OT_subtool_delete,
    SCULPTEXT_OT_subtool_move,
    SCULPTEXT_OT_subtool_group_new,
    SCULPTEXT_OT_subtool_move_to_group,
    SCULPTEXT_OT_subtool_toggle_expand,
    SCULPTEXT_OT_subtool_merge,
    SCULPTEXT_OT_subtool_split_loose,
    SCULPTEXT_OT_subtool_add,
    SCULPTEXT_OT_subtool_mirror,
    SCULPTEXT_OT_subtool_show_all,
    SCULPTEXT_OT_subtool_frame_active,
    SCULPTEXT_OT_subtool_split_faceset,
    SCULPTEXT_OT_subtool_split_mask,
    SCULPTEXT_OT_subtool_multires_step,
    SCULPTEXT_OT_subtool_bool_cycle_op,
    SCULPTEXT_OT_subtool_bool_preview,
    SCULPTEXT_OT_subtool_bool_apply,
    SCULPTEXT_OT_subtool_bool_direct,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
