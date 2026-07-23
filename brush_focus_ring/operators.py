"""Operador modal que sigue el ratón y activa/desactiva el dibujo."""

import bpy
from bpy.app.translations import pgettext_rpt as rpt_
from bpy.props import IntProperty, StringProperty

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
    """Toggles the double focus/influence circle"""

    bl_idname = "sculpt_ext.focus_ring_toggle"
    bl_label = "Focus Ring"
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
            self.report({'WARNING'}, rpt_("Could not apply the focus to the active brush"))
        self._maybe_hide_native_cursor(context)
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, rpt_("Focus ring enabled"))
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
        elif event.value in {'PRESS', 'RELEASE'} and st["in_view3d"]:
            # Otro atajo (tamaño de pincel con +/-, foco, etc.) pudo cambiar el
            # pincel: repintar el anillo para que refleje el nuevo radio al
            # instante, sin esperar a mover el ratón. El evento igualmente pasa.
            utils.tag_redraw_view3d(context)

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
        self.report({'INFO'}, rpt_("Focus ring disabled"))


class SCULPT_EXT_OT_focus_adjust(bpy.types.Operator):
    """Raises or lowers the focus one step (optional keyboard shortcut)"""

    bl_idname = "sculpt_ext.focus_adjust"
    bl_label = "Adjust Focus"
    bl_options = {'REGISTER', 'UNDO'}

    direction: IntProperty(
        name="Direction",
        description="+1 raises the focus, -1 lowers it",
        default=1,
    )

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        prefs = utils.get_prefs(context)
        step = prefs.focus_step if prefs is not None else 0.05
        sign = 1 if self.direction >= 0 else -1
        current = context.scene.bfr_focus
        new_value = max(0.0, min(1.0, current + sign * step))
        # Escribir la propiedad dispara _on_focus_update: aplica al pincel y redibuja.
        context.scene.bfr_focus = new_value
        self.report({'INFO'}, rpt_("Focus: {:.2f}").format(new_value))
        return {'FINISHED'}


class SCULPT_EXT_OT_strength_adjust(bpy.types.Operator):
    """Raises or lowers the brush strength one step (optional keyboard shortcut)"""

    bl_idname = "sculpt_ext.strength_adjust"
    bl_label = "Adjust Strength"
    bl_options = {'REGISTER', 'UNDO'}

    direction: IntProperty(
        name="Direction",
        description="+1 raises the strength, -1 lowers it",
        default=1,
    )

    @classmethod
    def poll(cls, context):
        return utils.get_active_brush(context) is not None

    def execute(self, context):
        paint = utils.get_active_paint(context)
        brush = paint.brush if paint is not None else None
        if brush is None:
            return {'CANCELLED'}
        prefs = utils.get_prefs(context)
        step = prefs.focus_step if prefs is not None else 0.05
        sign = 1 if self.direction >= 0 else -1
        current = utils.get_brush_strength(context, paint, brush)
        new_value = max(0.0, current + sign * step)
        # Tope en 1.0 al subir, pero sin recortar valores >1 ya existentes.
        if sign > 0:
            new_value = min(new_value, max(1.0, current))
        utils.set_brush_strength(context, paint, brush, new_value)
        utils.tag_redraw_view3d(context)
        self.report({'INFO'}, rpt_("Strength: {:.2f}").format(new_value))
        return {'FINISHED'}


class SCULPT_EXT_OT_capture_key(bpy.types.Operator):
    """Waits for a key press and assigns it to the shortcut field"""

    bl_idname = "sculpt_ext.capture_key"
    bl_label = "Capture Key"
    bl_options = {'INTERNAL'}

    # Nombre de la propiedad de preferencias a rellenar (p. ej. "key_down").
    target: StringProperty()

    # Teclas ignoradas mientras se espera: ratón y modificadores sueltos.
    _IGNORE = frozenset({
        'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE',
        'LEFTMOUSE', 'RIGHTMOUSE', 'MIDDLEMOUSE',
        'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'WHEELINMOUSE', 'WHEELOUTMOUSE',
        'LEFT_CTRL', 'RIGHT_CTRL', 'LEFT_ALT', 'RIGHT_ALT',
        'LEFT_SHIFT', 'RIGHT_SHIFT', 'OSKEY',
    })

    def invoke(self, context, event):
        prefs = utils.get_prefs(context)
        if prefs is None or not hasattr(prefs, self.target):
            return {'CANCELLED'}
        context.window_manager.modal_handler_add(self)
        self.report(
            {'INFO'},
            rpt_("Press a key combination to assign it (Esc to cancel)"),
        )
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.value != 'PRESS' or event.type in self._IGNORE:
            return {'RUNNING_MODAL'}
        if event.type == 'ESC':
            self.report({'INFO'}, rpt_("Capture cancelled"))
            return {'CANCELLED'}
        prefs = utils.get_prefs(context)
        if prefs is None:
            return {'CANCELLED'}
        try:
            # Asignar dispara el update de la propiedad: reconstruye los atajos.
            setattr(prefs, self.target, event.type)
        except (TypeError, ValueError):
            self.report(
                {'WARNING'},
                rpt_("Key not assignable: {}").format(event.type),
            )
            return {'RUNNING_MODAL'}
        # Cada tecla tiene sus propios modificadores: guardar la combinación
        # pulsada (Ctrl/Alt/Shift) en las propiedades de ESA tecla.
        setattr(prefs, self.target + "_ctrl", event.ctrl)
        setattr(prefs, self.target + "_alt", event.alt)
        setattr(prefs, self.target + "_shift", event.shift)
        self.report(
            {'INFO'},
            rpt_("Key assigned: {}").format(self._combo_label(event)),
        )
        return {'FINISHED'}

    @staticmethod
    def _combo_label(event) -> str:
        """Texto legible de la combinación, p. ej. 'Ctrl+Shift+D'."""
        parts = []
        if event.ctrl:
            parts.append("Ctrl")
        if event.alt:
            parts.append("Alt")
        if event.shift:
            parts.append("Shift")
        parts.append(event.type)
        return "+".join(parts)


classes = (
    SCULPT_EXT_OT_focus_ring_toggle,
    SCULPT_EXT_OT_focus_adjust,
    SCULPT_EXT_OT_strength_adjust,
    SCULPT_EXT_OT_capture_key,
)
