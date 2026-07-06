"""Preferencias del addon: colores, grosor y comportamiento."""

import bpy
from bpy.props import BoolProperty, FloatProperty, FloatVectorProperty


class BrushFocusRingPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    outer_color: FloatVectorProperty(
        name="Color exterior (influencia)",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 0.35, 0.1, 0.9),
    )
    inner_color: FloatVectorProperty(
        name="Color interior (foco)",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.9),
    )
    line_width: FloatProperty(
        name="Grosor de línea",
        min=1.0,
        max=5.0,
        default=1.5,
    )
    min_inner_ratio: FloatProperty(
        name="Radio interior mínimo",
        description="Fracción del radio exterior visible aunque el foco sea 0",
        min=0.0,
        max=0.5,
        default=0.05,
    )
    hide_native_cursor: BoolProperty(
        name="Ocultar cursor nativo en Sculpt",
        description="Desactiva el círculo de Blender mientras el anillo está activo",
        default=True,
    )

    def draw(self, context):
        col = self.layout.column()
        col.prop(self, "outer_color")
        col.prop(self, "inner_color")
        col.prop(self, "line_width")
        col.prop(self, "min_inner_ratio")
        col.prop(self, "hide_native_cursor")


classes = (BrushFocusRingPreferences,)
