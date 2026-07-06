"""Panel lateral y slider de cabecera: control del foco y estado."""

import bpy

from . import utils


class VIEW3D_PT_brush_focus_ring(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Subdiv'
    bl_label = 'Anillo de foco'

    def draw(self, context):
        layout = self.layout
        st = utils.state

        icon = 'PAUSE' if st["running"] else 'PLAY'
        text = 'Desactivar anillo' if st["running"] else 'Activar anillo'
        layout.operator("sculpt_ext.focus_ring_toggle", text=text, icon=icon)

        brush = utils.get_active_brush(context)
        if brush is None:
            layout.label(text="Sin pincel activo", icon='INFO')
            return

        radii = utils.compute_radii(context)
        if radii is not None:
            outer, inner = radii
            col = layout.column(align=True)
            col.label(text=f"Influencia (Size): {outer:.0f} px")
            col.label(text=f"Foco: {inner:.0f} px")

        layout.prop(context.scene, "bfr_focus", text="Foco", slider=True)


def draw_header_focus(self, context):
    """Slider 'Foco' en la cabecera del viewport, junto a Size/Strength."""
    if context.mode in {'SCULPT', 'PAINT_VERTEX', 'PAINT_WEIGHT', 'PAINT_TEXTURE'}:
        row = self.layout.row(align=True)
        row.scale_x = 0.9
        row.prop(context.scene, "bfr_focus", text="Foco", slider=True)
        self.layout.separator()


classes = (VIEW3D_PT_brush_focus_ring,)
