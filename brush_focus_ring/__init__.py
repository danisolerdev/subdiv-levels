"""Brush Focus Ring: doble circunferencia de pincel estilo ZBrush.

Interior = foco (propiedad propia, estilo Focal Shift).
Exterior = límite de influencia (tamaño del pincel).
"""

import bpy
from bpy.props import FloatProperty

from . import draw, keymaps, operators, preferences, translations, ui, utils

_modules = (preferences, operators, ui)


def _on_focus_update(self, context):
    utils.apply_focus_to_brush(context)
    utils.tag_redraw_view3d(context)


def register():
    translations.register()
    bpy.types.Scene.bfr_focus = FloatProperty(
        name="Focus",
        description="Radius of the central circle (focus) as a fraction of the outer one",
        min=0.0,
        max=1.0,
        default=0.5,
        update=_on_focus_update,
    )
    for module in _modules:
        for cls in module.classes:
            bpy.utils.register_class(cls)
    # append: se dibuja tras los popovers del pincel (Cursor, etc.).
    bpy.types.VIEW3D_HT_tool_header.append(ui.draw_header_focus)
    keymaps.register()


def unregister():
    # Apagar el modal si sigue vivo y limpiar el draw handler.
    utils.state["running"] = False
    draw.remove_handler()
    keymaps.unregister()
    bpy.types.VIEW3D_HT_tool_header.remove(ui.draw_header_focus)
    for module in reversed(_modules):
        for cls in reversed(module.classes):
            bpy.utils.unregister_class(cls)
    del bpy.types.Scene.bfr_focus
    translations.unregister()