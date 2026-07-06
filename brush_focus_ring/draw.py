"""Dibujo GPU de las dos circunferencias (POST_PIXEL, coords de región)."""

import math

import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from . import utils

_SEGMENTS = 64


def _circle_points(cx, cy, radius):
    step = 2.0 * math.pi / _SEGMENTS
    return [
        (cx + math.cos(i * step) * radius, cy + math.sin(i * step) * radius)
        for i in range(_SEGMENTS + 1)
    ]


def _draw_circle(shader, cx, cy, radius, color, width):
    batch = batch_for_shader(
        shader, 'LINE_STRIP', {"pos": _circle_points(cx, cy, radius)}
    )
    gpu.state.line_width_set(width)
    shader.uniform_float("color", color)
    batch.draw(shader)


def draw_callback():
    """Callback POST_PIXEL: dibuja foco (interior) e influencia (exterior)."""
    context = bpy.context
    st = utils.state
    if not st["running"] or not st["in_view3d"]:
        return
    region = context.region
    if region is None or region.as_pointer() != st["region_id"]:
        return
    if context.mode not in {'SCULPT', 'PAINT_VERTEX', 'PAINT_WEIGHT', 'PAINT_TEXTURE'}:
        return
    radii = utils.compute_radii(context)
    if radii is None:
        return
    outer, inner = radii
    prefs = utils.get_prefs(context)
    if prefs is None:
        return

    cx, cy = st["mouse"]
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')

    _draw_circle(shader, cx, cy, outer, tuple(prefs.outer_color), prefs.line_width)
    _draw_circle(shader, cx, cy, inner, tuple(prefs.inner_color), prefs.line_width)

    gpu.state.blend_set('NONE')
    gpu.state.line_width_set(1.0)


def add_handler():
    st = utils.state
    if st["draw_handler"] is None:
        st["draw_handler"] = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback, (), 'WINDOW', 'POST_PIXEL'
        )


def remove_handler():
    st = utils.state
    if st["draw_handler"] is not None:
        bpy.types.SpaceView3D.draw_handler_remove(st["draw_handler"], 'WINDOW')
        st["draw_handler"] = None
