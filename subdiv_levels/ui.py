"""Panel lateral (N) del addon Subdiv Levels."""

import bpy
from bpy.app.translations import pgettext_iface as iface_

from . import utils


class SCULPTEXT_PT_subdiv(bpy.types.Panel):
    bl_label = "Subdiv Levels"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Subdiv"

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT', 'SCULPT'}

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj is None or obj.type != 'MESH':
            layout.label(text="Select a mesh", icon='INFO')
            return

        mod = utils.get_multires(obj)

        if mod is None:
            col = layout.column()
            col.scale_y = 1.5
            col.operator(
                "sculpt_ext.subdiv_smart", text="Add Multires", icon='MOD_MULTIRES'
            )
            return

        level = mod.sculpt_levels
        total = mod.total_levels

        # Nivel actual + botones − / +
        row = layout.row(align=True)
        row.label(text=iface_("Level {} / {}").format(level, total), translate=False)
        row.operator("sculpt_ext.level_down", text="", icon='REMOVE')
        row.operator("sculpt_ext.level_up", text="", icon='ADD')

        # Botón principal
        col = layout.column()
        col.scale_y = 1.4
        col.operator(
            "sculpt_ext.subdiv_smart", text="Subdivide (Ctrl+D)", icon='MOD_MULTIRES'
        )

        # Caja plegable "Avanzado"
        header, body = layout.panel("sculpt_ext_advanced", default_closed=True)
        header.label(text="Advanced")
        if body is not None:
            col = body.column()
            col.operator("sculpt_ext.delete_higher", icon='TRASH')
            col.operator("sculpt_ext.apply_base", icon='CHECKMARK')
            col.operator("sculpt_ext.apply_modifier", icon='FILE_TICK')
            col.separator()

            prefs = utils.get_prefs()
            if utils.prefs_are_real(prefs):
                col.prop(prefs, "subdivision_mode", text="Mode")
            col.separator()

            col.prop(mod, "levels", text="Viewport")
            col.prop(mod, "render_levels", text="Render")

            # Hueco fase 2: reconstruir niveles inferiores (multires_rebuild_subdiv).

        # Pie: recuento de caras estimado
        faces = utils.estimate_faces(obj, level)
        layout.label(
            text=iface_("Faces (approx.): {}").format(utils.format_faces(faces)),
            translate=False,
        )


classes = (
    SCULPTEXT_PT_subdiv,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
