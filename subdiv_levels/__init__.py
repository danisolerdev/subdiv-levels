"""Subdiv Levels — niveles de subdivisión estilo ZBrush/Nomad para Blender.

Extensión (Blender 4.2+ / 5.x): los metadatos viven en blender_manifest.toml,
no se usa bl_info.
"""

from . import translations, preferences, operators, ui, keymaps

_modules = (translations, preferences, operators, ui, keymaps)


def register():
    for module in _modules:
        module.register()


def unregister():
    for module in reversed(_modules):
        module.unregister()
