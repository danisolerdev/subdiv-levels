"""Helpers del puente: acceso al pincel, tamano y foco.

Respeta Unified Paint Settings para el tamano y se integra con el addon
`brush_focus_ring` (propiedad de escena `bfr_focus`) si esta activo; si no,
escribe directamente en `brush.hardness`.
"""

import bpy

SIZE_MIN = 1
SIZE_MAX = 5000


def get_prefs(context):
    """Preferencias del addon, o valores por defecto si no estan disponibles."""
    addon = context.preferences.addons.get(__package__)
    if addon is not None and addon.preferences is not None:
        return addon.preferences
    return _FallbackPrefs()


class _FallbackPrefs:
    """Valores por defecto cuando las preferencias reales no existen."""

    enable_hotkeys = True
    size_factor = 1.15
    focus_step = 0.05


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
    """Pincel activo del modo actual, o None."""
    paint = get_active_paint(context)
    return paint.brush if paint is not None else None


def _get_unified_settings(context, paint):
    """UnifiedPaintSettings, compatible con su ubicacion en 4.x y 5.x."""
    ups = getattr(paint, "unified_paint_settings", None)
    if ups is None:
        ups = getattr(context.tool_settings, "unified_paint_settings", None)
    return ups


def nudge_brush_size(context, factor: float):
    """Multiplica el tamano del pincel por `factor` con clamp. Devuelve px o None.

    Escribe en Unified Paint Settings si el tamano esta unificado; si no, en
    el propio pincel. Garantiza un cambio minimo de 1 px para que los pasos
    pequenos no se pierdan por el redondeo.
    """
    paint = get_active_paint(context)
    if paint is None or paint.brush is None:
        return None
    brush = paint.brush
    ups = _get_unified_settings(context, paint)
    unified = ups is not None and getattr(ups, "use_unified_size", False)
    current = ups.size if unified else brush.size

    new_size = int(round(current * factor))
    if new_size == current:
        new_size = current + (1 if factor > 1.0 else -1)
    new_size = max(SIZE_MIN, min(SIZE_MAX, new_size))

    if unified:
        ups.size = new_size
    else:
        brush.size = new_size
    return new_size


def nudge_focus(context, delta: float):
    """Suma `delta` al foco con clamp [0, 1]. Devuelve el valor o None.

    Prefiere la propiedad de escena `bfr_focus` (addon Brush Focus Ring), cuyo
    callback ya aplica el foco al pincel y redibuja el anillo. Si no existe,
    escribe directamente en `brush.hardness`.
    """
    scene = context.scene
    if hasattr(scene, "bfr_focus"):
        value = max(0.0, min(1.0, scene.bfr_focus + delta))
        scene.bfr_focus = value
        return value

    brush = get_active_brush(context)
    if brush is None or not hasattr(brush, "hardness"):
        return None
    value = max(0.0, min(1.0, brush.hardness + delta))
    brush.hardness = value
    return value
