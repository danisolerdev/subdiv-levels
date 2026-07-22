"""Preferencias del addon: paso de los encoders y activacion de atajos."""

import bpy
from bpy.props import BoolProperty, FloatProperty


class MacropadBridgePreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    enable_hotkeys: BoolProperty(
        name="Activar atajos del macropad",
        description="Registra los atajos que enlazan los encoders del macropad",
        default=True,
    )
    size_factor: FloatProperty(
        name="Paso de tamano (factor)",
        description="Cada muesca del encoder multiplica/divide el tamano por este factor",
        min=1.01,
        max=2.0,
        default=1.15,
    )
    focus_step: FloatProperty(
        name="Paso de foco",
        description="Cuanto sube o baja el foco (dureza) por muesca del encoder",
        min=0.01,
        max=0.5,
        default=0.05,
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "enable_hotkeys")
        col.prop(self, "size_factor")
        col.prop(self, "focus_step")

        box = layout.box()
        box.label(text="Mapa de encoders (el macropad debe enviar estas teclas):")
        box.label(text="Todas con Ctrl+Alt+Shift + letra.", icon='INFO')
        rows = (
            ("Encoder 1 - Tamano", "+Q (subir)", "+A (bajar)"),
            ("Encoder 2 - Subdivision", "+W (subir)", "+S (bajar)"),
            ("Encoder 3 - Foco", "+E (subir)", "+D (bajar)"),
            ("Encoder 4 - Deshacer/Rehacer", "+R (rehacer)", "+F (deshacer)"),
        )
        for name, cw, ccw in rows:
            row = box.row()
            row.label(text=name)
            row.label(text=cw)
            row.label(text=ccw)
        box.label(
            text="Cambia atajos en Preferencias > Keymap > filtra por 'macropad'.",
            icon='INFO',
        )


classes = (MacropadBridgePreferences,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
