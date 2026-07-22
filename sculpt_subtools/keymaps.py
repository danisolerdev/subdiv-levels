"""Registro y limpieza de atajos del addon Sculpt Subtools.

Por defecto desactivados (el keymap de Sculpt está muy poblado). Si se activan
en preferencias:

Alt+Up   → sculpt_ext.subtool_cycle(direction='PREV')   (solo Sculpt)
Alt+Down → sculpt_ext.subtool_cycle(direction='NEXT')   (solo Sculpt)
"""

import bpy

from . import utils

# Pares (keymap, keymap_item) creados por el addon, para limpiarlos en unregister().
addon_keymaps = []


def register_keymaps():
    """Crea los atajos si están habilitados en las preferencias."""
    prefs = utils.get_prefs()
    if not prefs.enable_hotkeys:
        return

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc is None:  # modo background: no hay keyconfig de addon
        return

    km = kc.keymaps.new(name="Sculpt", space_type='EMPTY')
    for direction, key in (('PREV', 'UP_ARROW'), ('NEXT', 'DOWN_ARROW')):
        kmi = km.keymap_items.new(
            "sculpt_ext.subtool_cycle", key, 'PRESS', alt=True
        )
        kmi.properties.direction = direction
        addon_keymaps.append((km, kmi))


def unregister_keymaps():
    """Elimina todos los atajos creados por el addon."""
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


def register():
    register_keymaps()


def unregister():
    unregister_keymaps()
