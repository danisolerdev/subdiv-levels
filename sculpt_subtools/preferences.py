"""Preferencias del addon Sculpt Subtools."""

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty


def _update_hotkeys(self, context):
    """Reconstruye los keymaps al activar/desactivar los atajos."""
    from . import keymaps
    keymaps.unregister_keymaps()
    if self.enable_hotkeys:
        keymaps.register_keymaps()


class SculptSubtoolsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    switch_reenters_sculpt: BoolProperty(
        name="Reentrar en Sculpt al saltar",
        description="Al activar otro subtool desde Sculpt, volver a modo Sculpt "
        "(si se desactiva, el salto deja el objeto en modo Objeto)",
        default=True,
    )
    solo_includes_group: BoolProperty(
        name="Solo incluye el grupo",
        description="Al aislar (Solo), mantener visible todo el grupo del subtool, "
        "no solo el objeto",
        default=False,
    )
    confirm_delete: BoolProperty(
        name="Confirmar borrado",
        description="Pedir confirmación antes de borrar un subtool",
        default=True,
    )
    confirm_merge: BoolProperty(
        name="Confirmar unión",
        description="Pedir confirmación antes de unir subtools",
        default=True,
    )
    enable_hotkeys: BoolProperty(
        name="Activar atajos",
        description="Registrar los atajos para ciclar subtools (Alt+↑ / Alt+↓)",
        default=False,
        update=_update_hotkeys,
    )
    sort_mode: EnumProperty(
        name="Orden de la lista",
        description="Cómo ordenar los subtools dentro de cada grupo",
        items=(
            ('MANUAL', "Manual", "Por el orden asignado (subir/bajar)"),
            ('NAME', "Nombre", "Alfabético por nombre"),
        ),
        default='MANUAL',
    )
    show_thumbnails: BoolProperty(
        name="Mostrar miniaturas",
        description="Dibujar una miniatura de cada subtool en la paleta "
        "(estilo ZBrush). Requiere GPU",
        default=True,
    )
    auto_thumbnails: BoolProperty(
        name="Miniaturas automáticas",
        description="Regenerar la miniatura al salir de un subtool y al "
        "crear/duplicar/separar. Desactívalo si notas tirones al esculpir",
        default=True,
    )
    thumbnail_scale: FloatProperty(
        name="Tamaño de miniatura",
        description="Escala de la miniatura en la paleta",
        default=3.0,
        min=1.0,
        max=8.0,
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "switch_reenters_sculpt")
        col.prop(self, "solo_includes_group")
        col.prop(self, "sort_mode")
        col.separator()
        col.prop(self, "confirm_delete")
        col.prop(self, "confirm_merge")
        col.separator()
        col.prop(self, "show_thumbnails")
        sub = col.column()
        sub.enabled = self.show_thumbnails
        sub.prop(self, "auto_thumbnails")
        sub.prop(self, "thumbnail_scale")
        col.separator()
        col.prop(self, "enable_hotkeys")


classes = (
    SculptSubtoolsPreferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
