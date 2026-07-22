"""Operadores del puente de macropad (prefijo macropad.*).

Solo se implementan aqui las acciones que Blender no expone como operador
directo de un solo paso: ajustar el tamano del pincel y el foco. La
subdivision reutiliza los operadores de `subdiv_levels` y deshacer/rehacer
usan los nativos `ed.undo` / `ed.redo` (se enlazan en keymaps.py).
"""

import bpy
from bpy.props import BoolProperty

from . import utils


def _poll_sculpt_or_paint(context) -> bool:
    """Hay un modo de pintura/escultura activo con pincel."""
    return utils.get_active_paint(context) is not None


class MACROPAD_OT_brush_size(bpy.types.Operator):
    """Sube o baja el tamano del pincel de forma multiplicativa (encoder)"""

    bl_idname = "macropad.brush_size"
    bl_label = "Tamano de pincel +/-"
    bl_options = {'REGISTER'}

    up: BoolProperty(name="Subir", default=True)

    @classmethod
    def poll(cls, context):
        return _poll_sculpt_or_paint(context)

    def execute(self, context):
        prefs = utils.get_prefs(context)
        factor = prefs.size_factor if self.up else 1.0 / prefs.size_factor
        new_size = utils.nudge_brush_size(context, factor)
        if new_size is None:
            self.report({'WARNING'}, "No hay pincel activo")
            return {'CANCELLED'}
        self.report({'INFO'}, f"Tamano: {new_size} px")
        return {'FINISHED'}


class MACROPAD_OT_focus(bpy.types.Operator):
    """Sube o baja el foco (dureza) del pincel activo (encoder)"""

    bl_idname = "macropad.focus"
    bl_label = "Foco +/-"
    bl_options = {'REGISTER'}

    up: BoolProperty(name="Subir", default=True)

    @classmethod
    def poll(cls, context):
        return _poll_sculpt_or_paint(context)

    def execute(self, context):
        prefs = utils.get_prefs(context)
        delta = prefs.focus_step if self.up else -prefs.focus_step
        new_focus = utils.nudge_focus(context, delta)
        if new_focus is None:
            self.report({'WARNING'}, "El pincel activo no admite foco (hardness)")
            return {'CANCELLED'}
        self.report({'INFO'}, f"Foco: {new_focus:.2f}")
        return {'FINISHED'}


classes = (
    MACROPAD_OT_brush_size,
    MACROPAD_OT_focus,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
