"""Sculpt Subtools — paleta de subtools estilo ZBrush para Blender 5.x.

Extensión (Blender 4.2+ / 5.x): los metadatos viven en blender_manifest.toml,
no se usa bl_info. Cada objeto malla es un subtool y cada colección un "Tool";
el addon solo aporta la UX/paleta, no un modelo de datos propio.
"""

from . import properties, preferences, preview, operators, ui, keymaps

# Orden de registro: propiedades primero (las usan operadores y panel), luego
# preferencias, la caché de miniaturas, operadores, UI y atajos.
_modules = (properties, preferences, preview, operators, ui, keymaps)


def register():
    for module in _modules:
        module.register()


def unregister():
    for module in reversed(_modules):
        module.unregister()
