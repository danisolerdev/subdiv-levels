"""Operadores del addon Subdiv Levels (prefijo sculpt_ext.*)."""

import bpy
from bpy.app.translations import pgettext_rpt as rpt_
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
    """Go up a level; creates the modifier or a new level if needed (Ctrl+D)"""

    bl_idname = "sculpt_ext.subdiv_smart"
    bl_label = "Smart Subdivide"
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
            self.report({'INFO'}, rpt_("Level {} / {}").format(level, mod.total_levels))
            return {'FINISHED'}

        if mod.sculpt_levels >= prefs.max_auto_level:
            self.report(
                {'WARNING'},
                rpt_(
                    "Safety limit: level {} ≥ automatic maximum ({}). "
                    "Raise it in the preferences."
                ).format(mod.sculpt_levels, prefs.max_auto_level),
            )
            return {'CANCELLED'}

        return self._subdivide(context, obj, mod, prefs)

    def _subdivide(self, context, obj, mod, prefs):
        """Añade un nivel nuevo con el modo de las preferencias y lo activa."""
        result = bpy.ops.object.multires_subdivide(
            modifier=mod.name, mode=prefs.subdivision_mode
        )
        if 'FINISHED' not in result:
            self.report({'WARNING'}, rpt_("Could not subdivide the modifier"))
            return {'CANCELLED'}
        level = utils.set_level(obj, mod, mod.total_levels, prefs)
        _redraw(context)
        self.report(
            {'INFO'}, rpt_("Level {} / {} (new)").format(level, mod.total_levels)
        )
        return {'FINISHED'}


class SCULPTEXT_OT_level_up(bpy.types.Operator):
    """Goes up one subdivision level without creating new levels (Alt+D)"""

    bl_idname = "sculpt_ext.level_up"
    bl_label = "Level Up"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_multires(context)

    def execute(self, context):
        obj = context.object
        mod = utils.get_multires(obj)
        if mod.sculpt_levels >= mod.total_levels:
            self.report(
                {'INFO'},
                rpt_("Already at the maximum level ({})").format(mod.total_levels),
            )
            return {'CANCELLED'}
        level = utils.set_level(obj, mod, mod.sculpt_levels + 1)
        _redraw(context)
        self.report({'INFO'}, rpt_("Level {} / {}").format(level, mod.total_levels))
        return {'FINISHED'}


class SCULPTEXT_OT_level_down(bpy.types.Operator):
    """Goes down one subdivision level without destroying anything (Shift+D)"""

    bl_idname = "sculpt_ext.level_down"
    bl_label = "Level Down"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_multires(context)

    def execute(self, context):
        obj = context.object
        mod = utils.get_multires(obj)
        if mod.sculpt_levels <= 0:
            self.report({'INFO'}, rpt_("Already at the base level (0)"))
            return {'CANCELLED'}
        level = utils.set_level(obj, mod, mod.sculpt_levels - 1)
        _redraw(context)
        self.report({'INFO'}, rpt_("Level {} / {}").format(level, mod.total_levels))
        return {'FINISHED'}


class SCULPTEXT_OT_level_set(bpy.types.Operator):
    """Sets the exact subdivision level"""

    bl_idname = "sculpt_ext.level_set"
    bl_label = "Set Level"
    bl_options = {'REGISTER', 'UNDO'}

    level: IntProperty(name="Level", default=0, min=0)

    @classmethod
    def poll(cls, context):
        return _poll_multires(context)

    def execute(self, context):
        obj = context.object
        mod = utils.get_multires(obj)
        level = utils.set_level(obj, mod, self.level)
        _redraw(context)
        self.report({'INFO'}, rpt_("Level {} / {}").format(level, mod.total_levels))
        return {'FINISHED'}


class SCULPTEXT_OT_delete_higher(bpy.types.Operator):
    """Deletes the subdivision levels above the current one"""

    bl_idname = "sculpt_ext.delete_higher"
    bl_label = "Delete Higher Levels"
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
            self.report({'WARNING'}, rpt_("Could not delete the higher levels"))
            return {'CANCELLED'}
        utils.set_level(obj, mod, mod.total_levels)
        _redraw(context)
        self.report(
            {'INFO'},
            rpt_("Higher levels deleted ({} remaining)").format(mod.total_levels),
        )
        return {'FINISHED'}


class SCULPTEXT_OT_apply_base(bpy.types.Operator):
    """Applies the current level's displacement to the base mesh"""

    bl_idname = "sculpt_ext.apply_base"
    bl_label = "Apply Base"
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
            self.report({'WARNING'}, rpt_("Could not apply the base"))
            return {'CANCELLED'}
        _redraw(context)
        self.report({'INFO'}, rpt_("Displacement applied to the base mesh"))
        return {'FINISHED'}



class SCULPTEXT_OT_apply_modifier(bpy.types.Operator):
    """Fixes the mesh at the current level and removes the Multires (collapse)"""

    bl_idname = "sculpt_ext.apply_modifier"
    bl_label = "Apply Modifier"
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
            self.report(
                {'WARNING'}, rpt_("Could not apply the modifier: {}").format(error)
            )
            result = {'CANCELLED'}
        if previous_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=previous_mode)
        if 'FINISHED' not in result:
            return {'CANCELLED'}
        _redraw(context)
        self.report(
            {'INFO'}, rpt_("Multires applied: the mesh is now fixed at the current level")
        )
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
