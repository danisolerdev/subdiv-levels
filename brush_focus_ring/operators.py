"""Operador modal que sigue el ratón y activa/desactiva el dibujo."""

import bpy

from . import draw, utils


def _region_under_mouse(context, mx, my):
    """(region, área es VIEW_3D) para la posición del ratón en la ventana."""
    screen = context.screen
    if screen is None:
        return None, False
    for area in screen.areas:
        if area.type != 'VIEW_3D':
            continue
        for region in area.regions:
            if region.type != 'WINDOW':
                continue
            if (region.x <= mx < region.x + region.width
                    and region.y <= my < region.y + region.height):
                return region, True
    return None, False


class SCULPT_EXT_OT_focus_ring_toggle(bpy.types.Operator):
    """Activa o desactiva la doble circunferencia de foco/influencia"""

    bl_idname = "sculpt_ext.focus_ring_toggle"
    bl_label = "Anillo de foco"
    bl_options = {'REGISTER'}

    _native_cursor_backup = None

    @classmethod
    def poll(cls, context):
        return context.area is not None and context.window is not None

    def invoke(self, context, event):
        st = utils.state
        if st["running"]:
            # Segundo invoke = apagar: el modal activo lo detecta y termina.
            st["running"] = False
            utils.tag_redraw_view3d(context)
            return {'CANCELLED'}

        st["running"] = True
        st["mouse"] = (event.mouse_region_x, event.mouse_region_y)
        draw.add_handler()
        if not utils.apply_focus_to_brush(context):
            self.report({'WARNING'}, "No se pudo aplicar el foco al pincel activo")
        self._maybe_hide_native_cursor(context)
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "Anillo de foco activado")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        st = utils.state
        if not st["running"]:
            self._cleanup(context)
            return {'CANCELLED'}

        if event.type == 'MOUSEMOVE':
            region, in_v3d = _region_under_mouse(
                context, event.mouse_x, event.mouse_y
            )
            st["in_view3d"] = in_v3d
            if region is not None:
                st["region_id"] = region.as_pointer()
                st["mouse"] = (
                    event.mouse_x - region.x,
                    event.mouse_y - region.y,
                )
                region.tag_redraw()

        # Nunca consumir eventos: esculpir y navegar siguen funcionando.
        return {'PASS_THROUGH'}

    def _maybe_hide_native_cursor(self, context):
        prefs = utils.get_prefs(context)
        if prefs is None or not prefs.hide_native_cursor:
            return
        paint = context.tool_settings.sculpt
        if paint is not None:
            self._native_cursor_backup = paint.show_brush
            paint.show_brush = False

    def _restore_native_cursor(self, context):
        if self._native_cursor_backup is None:
            return
        paint = context.tool_settings.sculpt
        if paint is not None:
            paint.show_brush = self._native_cursor_backup
        self._native_cursor_backup = None

    def _cleanup(self, context):
        draw.remove_handler()
        self._restore_native_cursor(context)
        utils.state["in_view3d"] = False
        utils.tag_redraw_view3d(context)
        self.report({'INFO'}, "Anillo de foco desactivado")


classes = (SCULPT_EXT_OT_focus_ring_toggle,)
