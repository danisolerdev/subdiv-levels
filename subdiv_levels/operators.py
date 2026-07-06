"""Operadores del addon Subdiv Levels (prefijo sculpt_ext.*)."""

import bpy
from bpy.props import IntProperty

from . import utils


def _poll_mesh(context) -> bool:
    """Hay objeto activo, es malla y no está en modo Edit."""
    obj = context.object
    return obj is not None and obj.type == 'MESH' and obj.mode != 'EDIT'


def _poll_multires(context) -> bool:
    """Como _poll_mesh y además el objeto tiene modificador Multires."""
    return _poll_mesh(context) and utils.get_multires(context.object) is not None


def _redraw(context):
    """Fuerza el refresco del área activa tras cambiar propiedades desde un atajo."""
    if context.area is not None:
        context.area.tag_redraw()


class SCULPTEXT_OT_subdiv_smart(bpy.types.Operator):
    """Sube de nivel; crea el modificador o un nivel nuevo si hace falta (Ctrl+D)"""

    bl_idname = "sculpt_ext.subdiv_smart"
    bl_label = "Subdividir (inteligente)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_mesh(context)

    def execute(self, context):
        obj = context.object
        prefs = utils.get_prefs()
        mod = utils.get_multires(obj)

        if mod is None:
            # Crear el modificador y subir a nivel 1 en un solo gesto.
            mod = utils.create_multires(obj)
            return self._subdivide(context, obj, mod, prefs)

        if mod.sculpt_levels < mod.total_levels:
            level = utils.set_level(obj, mod, mod.sculpt_levels + 1, prefs)
            _redraw(context)
            self.report({'INFO'}, f"Nivel {level} / {mod.total_levels}")
            return {'FINISHED'}

        if mod.sculpt_levels >= prefs.max_auto_level:
            self.report(
                {'WARNING'},
                f"Límite de seguridad: nivel {mod.sculpt_levels} ≥ máximo "
                f"automático ({prefs.max_auto_level}). Súbelo en las preferencias.",
            )
            return {'CANCELLED'}

        return self._subdivide(context, obj, mod, prefs)

    def _subdivide(self, context, obj, mod, prefs):
        """Añade un nivel nuevo con el modo de las preferencias y lo activa."""
        result = bpy.ops.object.multires_subdivide(
            modifier=mod.name, mode=prefs.subdivision_mode
        )
        if 'FINISHED' not in result:
            self.report({'WARNING'}, "No se pudo subdividir el modificador")
            return {'CANCELLED'}
        level = utils.set_level(obj, mod, mod.total_levels, prefs)
        _redraw(context)
        self.report({'INFO'}, f"Nivel {level} / {mod.total_levels} (nuevo)")
        return {'FINISHED'}


class SCULPTEXT_OT_level_up(bpy.types.Operator):
    """Sube un nivel de subdivisión sin crear niveles nuevos (Alt+D)"""

    bl_idname = "sculpt_ext.level_up"
    bl_label = "Subir nivel"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_multires(context)

    def execute(self, context):
        obj = context.object
        mod = utils.get_multires(obj)
        if mod.sculpt_levels >= mod.total_levels:
            self.report({'INFO'}, f"Ya estás en el nivel máximo ({mod.total_levels})")
            return {'CANCELLED'}
        level = utils.set_level(obj, mod, mod.sculpt_levels + 1)
        _redraw(context)
        self.report({'INFO'}, f"Nivel {level} / {mod.total_levels}")
        return {'FINISHED'}


class SCULPTEXT_OT_level_down(bpy.types.Operator):
    """Baja un nivel de subdivisión sin destruir nada (Shift+D)"""

    bl_idname = "sculpt_ext.level_down"
    bl_label = "Bajar nivel"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_multires(context)

    def execute(self, context):
        obj = context.object
        mod = utils.get_multires(obj)
        if mod.sculpt_levels <= 0:
            self.report({'INFO'}, "Ya estás en el nivel base (0)")
            return {'CANCELLED'}
        level = utils.set_level(obj, mod, mod.sculpt_levels - 1)
        _redraw(context)
        self.report({'INFO'}, f"Nivel {level} / {mod.total_levels}")
        return {'FINISHED'}


class SCULPTEXT_OT_level_set(bpy.types.Operator):
    """Fija el nivel de subdivisión exacto"""

    bl_idname = "sculpt_ext.level_set"
    bl_label = "Fijar nivel"
    bl_options = {'REGISTER', 'UNDO'}

    level: IntProperty(name="Nivel", default=0, min=0)

    @classmethod
    def poll(cls, context):
        return _poll_multires(context)

    def execute(self, context):
        obj = context.object
        mod = utils.get_multires(obj)
        level = utils.set_level(obj, mod, self.level)
        _redraw(context)
        self.report({'INFO'}, f"Nivel {level} / {mod.total_levels}")
        return {'FINISHED'}


class SCULPTEXT_OT_delete_higher(bpy.types.Operator):
    """Borra los niveles de subdivisión por encima del actual"""

    bl_idname = "sculpt_ext.delete_higher"
    bl_label = "Borrar niveles superiores"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_multires(context)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        obj = context.object
        mod = utils.get_multires(obj)
        # El operador nativo borra por encima del nivel de viewport: alinearlo
        # con el nivel de sculpt antes de llamar.
        mod.levels = mod.sculpt_levels
        result = bpy.ops.object.multires_higher_levels_delete(modifier=mod.name)
        if 'FINISHED' not in result:
            self.report({'WARNING'}, "No se pudieron borrar los niveles superiores")
            return {'CANCELLED'}
        utils.set_level(obj, mod, mod.total_levels)
        _redraw(context)
        self.report({'INFO'}, f"Niveles superiores borrados ({mod.total_levels} restantes)")
        return {'FINISHED'}


class SCULPTEXT_OT_apply_base(bpy.types.Operator):
    """Aplica el desplazamiento del nivel actual a la malla base"""

    bl_idname = "sculpt_ext.apply_base"
    bl_label = "Aplicar base"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_multires(context)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        obj = context.object
        mod = utils.get_multires(obj)
        result = bpy.ops.object.multires_base_apply(modifier=mod.name)
        if 'FINISHED' not in result:
            self.report({'WARNING'}, "No se pudo aplicar la base")
            return {'CANCELLED'}
        _redraw(context)
        self.report({'INFO'}, "Desplazamiento aplicado a la malla base")
        return {'FINISHED'}



class SCULPTEXT_OT_apply_modifier(bpy.types.Operator):
    """Fija la malla al nivel actual y elimina el Multires (colapsar)"""

    bl_idname = "sculpt_ext.apply_modifier"
    bl_label = "Aplicar modificador"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_multires(context)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        obj = context.object
        mod = utils.get_multires(obj)
        # modifier_apply usa el nivel de viewport: alinearlo con el de sculpt.
        mod.levels = mod.sculpt_levels
        previous_mode = obj.mode
        if previous_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        try:
            result = bpy.ops.object.modifier_apply(modifier=mod.name)
        except RuntimeError as error:
            self.report({'WARNING'}, f"No se pudo aplicar el modificador: {error}")
            result = {'CANCELLED'}
        if previous_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=previous_mode)
        if 'FINISHED' not in result:
            return {'CANCELLED'}
        _redraw(context)
        self.report({'INFO'}, "Multires aplicado: la malla queda fija en el nivel actual")
        return {'FINISHED'}


classes = (
    SCULPTEXT_OT_subdiv_smart,
    SCULPTEXT_OT_level_up,
    SCULPTEXT_OT_level_down,
    SCULPTEXT_OT_level_set,
    SCULPTEXT_OT_delete_higher,
    SCULPTEXT_OT_apply_base,
    SCULPTEXT_OT_apply_modifier,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
