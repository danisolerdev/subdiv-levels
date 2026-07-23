"""Preferencias del addon Subdiv Levels."""

import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty


def _update_hotkeys(self, context):
    """Reconstruye los keymaps al activar/desactivar los atajos."""
    from . import keymaps
    keymaps.unregister_keymaps()
    if self.enable_hotkeys:
        keymaps.register_keymaps()


class SubdivLevelsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    subdivision_mode: EnumProperty(
        name="Subdivision Mode",
        description="Algorithm used when creating a new level",
        items=(
            ('CATMULL_CLARK', "Catmull-Clark", "Smooth subdivision (default)"),
            ('SIMPLE', "Simple", "Subdivides without smoothing"),
            ('LINEAR', "Linear", "Linear subdivision"),
        ),
        default='CATMULL_CLARK',
    )
    sync_viewport: BoolProperty(
        name="Sync Viewport",
        description="When changing level, also update the viewport level",
        default=True,
    )
    sync_render: BoolProperty(
        name="Sync Render",
        description="When changing level, also update the render level",
        default=False,
    )
    max_auto_level: IntProperty(
        name="Automatic Maximum Level",
        description="Ctrl+D does not create new levels above this level",
        default=7,
        min=1,
        max=10,
    )
    enable_hotkeys: BoolProperty(
        name="Enable Hotkeys",
        description="Register Ctrl+D / Shift+D / Alt+D",
        default=True,
        update=_update_hotkeys,
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "subdivision_mode")
        col.prop(self, "max_auto_level")
        col.separator()
        col.prop(self, "sync_viewport")
        col.prop(self, "sync_render")
        col.separator()
        col.prop(self, "enable_hotkeys")


classes = (
    SubdivLevelsPreferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
