"""Helpers: estado global, acceso al pincel y cálculo de radios."""

import bpy

# Estado compartido entre el operador modal y el draw handler.
state = {
    "running": False,       # el operador modal está activo
    "mouse": (0, 0),        # posición del ratón en coords de región
    "region_id": None,      # región bajo el ratón (para no dibujar en otras)
    "in_view3d": False,     # el ratón está dentro de un viewport 3D
    "draw_handler": None,   # handle devuelto por draw_handler_add
}


def get_prefs(context):
    """Devuelve las preferencias del addon o None."""
    addon = context.preferences.addons.get(__package__)
    return addon.preferences if addon else None


def get_active_paint(context):
    """Ajustes de pintura (Paint) del modo actual, o None."""
    ts = context.tool_settings
    mode = context.mode
    if mode == 'SCULPT':
        return ts.sculpt
    if mode == 'PAINT_VERTEX':
        return ts.vertex_paint
    if mode == 'PAINT_WEIGHT':
        return ts.weight_paint
    if mode == 'PAINT_TEXTURE':
        return ts.image_paint
    return None


def get_active_brush(context):
    """Pincel activo del modo de pintura/esculpido actual, o None."""
    paint = get_active_paint(context)
    return paint.brush if paint is not None else None


def _get_unified_settings(context, paint):
    """UnifiedPaintSettings, compatible con su ubicación en 4.x y 5.x."""
    ups = getattr(paint, "unified_paint_settings", None)
    if ups is None:
        ups = getattr(context.tool_settings, "unified_paint_settings", None)
    return ups


def get_brush_radius_px(context, paint, brush) -> int:
    """Radio del pincel en píxeles, respetando Unified Paint Settings."""
    ups = _get_unified_settings(context, paint)
    if ups is not None and getattr(ups, "use_unified_size", False):
        return ups.size
    return brush.size


def get_focus(context, brush) -> float:
    """Foco efectivo: la dureza (hardness) real del pincel activo.

    Si el pincel no tiene hardness, se usa la propiedad propia de escena.
    """
    value = getattr(brush, "hardness", None)
    if value is None:
        value = context.scene.bfr_focus
    return max(0.0, min(1.0, value))


def apply_focus_to_brush(context) -> bool:
    """Escribe el foco en la dureza (hardness) del pincel activo.

    hardness es el Focal Shift nativo: intensidad plena hasta esa fracción
    del radio y caída de ahí al borde. Devuelve False si no pudo aplicarse.
    """
    brush = get_active_brush(context)
    if brush is None:
        return False
    focus = max(0.0, min(1.0, context.scene.bfr_focus))
    if not hasattr(brush, "hardness"):
        return False
    try:
        brush.hardness = focus
    except (AttributeError, TypeError):
        return False
    return True


def compute_radii(context):
    """(radio_exterior, radio_interior) en px, o None si no hay pincel.

    Exterior: límite de influencia (Size de la cabecera).
    Interior: radio de intensidad plena = exterior x hardness del pincel.
    Se lee la dureza real, así el dibujo siempre refleja el comportamiento.
    """
    paint = get_active_paint(context)
    if paint is None or paint.brush is None:
        return None
    brush = paint.brush
    outer = float(get_brush_radius_px(context, paint, brush))
    if outer <= 0.0:
        return None
    focus = get_focus(context, brush)
    prefs = get_prefs(context)
    min_ratio = prefs.min_inner_ratio if prefs else 0.05
    inner = outer * max(focus, min_ratio)
    return outer, inner


def tag_redraw_view3d(context):
    """Redibuja todos los viewports 3D de la pantalla actual."""
    screen = context.screen
    if screen is None:
        return
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()
