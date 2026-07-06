"""Brush Focus Ring: doble circunferencia de pincel estilo ZBrush.

Interior = foco (propiedad propia, estilo Focal Shift).
Exterior = límite de influencia (tamaño del pincel).
"""

import bpy
from bpy.props import FloatProperty

from . import draw, operators, preferences, ui, utils

_modules = (preferences, operators, ui)


def _on_focus_update(self, context):
    utils.apply_focus_to_brush(context)
    utils.tag_redraw_view3d(context)


def register():
    bpy.types.Scene.bfr_focus = FloatProperty(
        name="Foco",
        description="Radio del círculo central (foco) como fracción del exterior",
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


def unregister():
    # Apagar el modal si sigue vivo y limpiar el draw handler.
    utils.state["running"] = False
    draw.remove_handler()
    bpy.types.VIEW3D_HT_tool_header.remove(ui.draw_header_focus)
    f