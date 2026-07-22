"""Macropad Bridge — enlaza los encoders de un macropad con acciones de Sculpt.

Extension (Blender 4.2+ / 5.x): los metadatos viven en blender_manifest.toml,
no se usa bl_info.

Los encoders envian F13-F20 y este addon los traduce a: tamano de pincel,
subdivision (reutiliza el addon subdiv_levels), foco (integra brush_focus_ring)
y deshacer/rehacer nativos.
"""

from . import preferences, operators, keymaps

_modules = (preferences, operators, keymaps)


def register():
    for module in _modules:
        module.register()


def unregister():
    for module in reversed(_modules):
        module.unregister()
