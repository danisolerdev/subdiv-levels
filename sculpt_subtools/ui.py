"""Paleta lateral (N) del addon Sculpt Subtools.

Dibuja el árbol Tool > Grupos > SubTools a mano (Blender no ofrece UIList en
árbol). No guarda estado propio: siempre refleja colecciones y objetos reales.
"""

import bpy

from . import preview, utils


class SCULPTEXT_PT_subtools(bpy.types.Panel):
    bl_label = "Sculpt Subtools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Subtools"

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT', 'SCULPT'}

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj is None or obj.type != 'MESH':
            layout.label(text="Selecciona una malla", icon='INFO')
            return

        prefs = utils.get_prefs()
        root = utils.get_tool_root(obj)

        # Cabecera: nombre del Tool + refrescar miniaturas + nuevo grupo.
        row = layout.row(align=True)
        row.label(text=root.name, icon='OUTLINER_COLLECTION')
        if prefs.show_thumbnails:
            row.operator("sculpt_ext.subtool_thumbnails_refresh", text="",
                         icon='FILE_REFRESH')
        row.operator("sculpt_ext.subtool_group_new", text="", icon='NEWFOLDER')

        # Árbol de subtools.
        box = layout.box()
        self._draw_collection(context, box, root, obj, prefs, depth=0)

        # Crear / espejar.
        row = layout.row(align=True)
        row.operator_menu_enum("sculpt_ext.subtool_add", "kind", text="Añadir",
                               icon='ADD')
        row.operator_menu_enum("sculpt_ext.subtool_mirror", "axis", text="Espejar",
                               icon='MOD_MIRROR')

        # Acciones sobre el subtool activo.
        col = layout.column(align=True)
        r = col.row(align=True)
        r.operator("sculpt_ext.subtool_duplicate", text="Duplicar", icon='DUPLICATE')
        r.operator("sculpt_ext.subtool_delete", text="Borrar", icon='TRASH')
        r = col.row(align=True)
        r.operator("sculpt_ext.subtool_move", text="Subir", icon='TRIA_UP').direction = 'UP'
        r.operator("sculpt_ext.subtool_move", text="Bajar", icon='TRIA_DOWN').direction = 'DOWN'
        r = col.row(align=True)
        r.operator("sculpt_ext.subtool_merge", text="Unir", icon='AUTOMERGE_ON')

        # Separar (splits).
        col = layout.column(align=True)
        col.label(text="Separar en subtools:")
        r = col.row(align=True)
        r.operator("sculpt_ext.subtool_split_loose", text="Sueltas")
        r.operator("sculpt_ext.subtool_split_mask", text="Máscara")
        r.operator("sculpt_ext.subtool_split_faceset", text="Face Sets")

        # Acciones globales.
        row = layout.row(align=True)
        row.operator("sculpt_ext.subtool_show_all", text="Mostrar todo", icon='HIDE_OFF')
        row.operator("sculpt_ext.subtool_frame_active", text="Enmarcar", icon='VIEWZOOM')

        # Nivel de Multires del subtool activo (integración con Subdiv Levels).
        mod = next((m for m in obj.modifiers if m.type == 'MULTIRES'), None)
        if mod is not None:
            box = layout.box()
            r = box.row(align=True)
            r.label(text=f"Multires  {mod.sculpt_levels} / {mod.total_levels}",
                    icon='MOD_MULTIRES')
            r.operator("sculpt_ext.subtool_multires_step", text="",
                       icon='REMOVE').delta = -1
            r.operator("sculpt_ext.subtool_multires_step", text="",
                       icon='ADD').delta = 1

        # Booleanas.
        scene = context.scene
        box = layout.box()
        r = box.row(align=True)
        r.label(text="Booleana", icon='MOD_BOOLEAN')
        r.prop(scene, "subtool_bool_edit", text="Roles", toggle=True)

        # Directas (usan la selección del viewport).
        r = box.row(align=True)
        r.operator("sculpt_ext.subtool_bool_direct", text="Unión").op = 'UNION'
        r.operator("sculpt_ext.subtool_bool_direct", text="Resta").op = 'DIFFERENCE'
        r.operator("sculpt_ext.subtool_bool_direct", text="Insec.").op = 'INTERSECT'

        # Live boolean (usa los roles por subtool).
        if scene.subtool_bool_active:
            box.operator("sculpt_ext.subtool_bool_preview", text="Quitar preview",
                         icon='LOOP_BACK', depress=True)
        else:
            box.operator("sculpt_ext.subtool_bool_preview", text="Preview en vivo",
                         icon='MOD_BOOLEAN')
        box.operator("sculpt_ext.subtool_bool_apply", text="Aplicar booleana",
                     icon='CHECKMARK')

        # Pie: recuento.
        chain = utils.all_subtools(root, prefs.sort_mode)
        faces = len(obj.data.polygons)
        layout.label(text=f"{len(chain)} subtools · {obj.name} ({faces} caras)")

    def _draw_collection(self, context, layout, coll, active_obj, prefs, depth):
        for o in utils.subtools_of(coll, prefs.sort_mode):
            self._draw_subtool_row(context, layout, o, active_obj, prefs, depth)
        for child in utils.child_groups(coll):
            self._draw_group_row(context, layout, child, active_obj, prefs, depth)

    def _draw_group_row(self, context, layout, coll, active_obj, prefs, depth):
        row = layout.row(align=True)
        self._indent(row, depth)
        icon = 'DISCLOSURE_TRI_DOWN' if coll.subtool_expanded else 'DISCLOSURE_TRI_RIGHT'
        op = row.operator("sculpt_ext.subtool_toggle_expand", text="", icon=icon,
                          emboss=False)
        op.collection = coll.name
        row.prop(coll, "hide_viewport", text="", emboss=False)
        row.label(text=coll.name, icon='FILE_FOLDER')
        op = row.operator("sculpt_ext.subtool_move_to_group", text="", icon='IMPORT')
        op.group = coll.name

        if coll.subtool_expanded:
            self._draw_collection(context, layout, coll, active_obj, prefs, depth + 1)

    def _draw_subtool_row(self, context, layout, obj, active_obj, prefs, depth):
        row = layout.row(align=True)
        self._indent(row, depth)

        # Miniatura a la izquierda (estilo ZBrush): la fila crece en alto.
        if prefs.show_thumbnails:
            row.template_icon(icon_value=preview.get_icon_id(obj),
                              scale=prefs.thumbnail_scale)

        # Columna de controles a la derecha de la miniatura.
        cell = row.column(align=True)

        # Fila superior: activar (nombre, resalta el activo) + renombrar.
        top = cell.row(align=True)
        is_active = obj == active_obj
        act_icon = 'RADIOBUT_ON' if is_active else 'RADIOBUT_OFF'
        op = top.operator("sculpt_ext.subtool_activate", text=obj.name, icon=act_icon,
                          depress=is_active)
        op.name = obj.name
        op = top.operator("sculpt_ext.subtool_rename", text="", icon='GREASEPENCIL',
                          emboss=False)
        op.target = obj.name

        # Fila inferior: visibilidad, rol booleano (si procede) y Solo.
        bottom = cell.row(align=True)
        vis_icon = 'HIDE_OFF' if not obj.hide_get() else 'HIDE_ON'
        op = bottom.operator("sculpt_ext.subtool_toggle_visible", text="", icon=vis_icon,
                             emboss=False)
        op.name = obj.name

        if context.scene.subtool_bool_edit:
            bool_icons = {
                'NONE': 'RADIOBUT_OFF', 'ADD': 'ADD',
                'SUBTRACT': 'REMOVE', 'INTERSECT': 'SELECT_INTERSECT',
            }
            op = bottom.operator("sculpt_ext.subtool_bool_cycle_op", text="",
                                 icon=bool_icons[obj.subtool_bool_op],
                                 depress=obj.subtool_bool_op != 'NONE')
            op.target = obj.name

        solo_on = context.scene.subtool_solo_active == obj.name
        solo_icon = 'PINNED' if solo_on else 'UNPINNED'
        op = bottom.operator("sculpt_ext.subtool_solo", text="", icon=solo_icon,
                             emboss=False)
        op.name = obj.name

    @staticmethod
    def _indent(row, depth):
        for _ in range(depth):
            row.label(text="", icon='BLANK1')


classes = (
    SCULPTEXT_PT_subtools,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
