"""Atajos del focus ring, pensados para dedicarle un encoder de macropad.

Cinco acciones, reconstruidas SIEMPRE desde las preferencias del addon (no desde
el sistema de diffs de keymap de Blender, que no persiste de forma fiable cuando
un mismo operador se usa en dos atajos, como aquí `focus_adjust` subir/bajar):

  bajar foco    (girar el encoder a la izquierda)
  activar/desactivar el anillo (pulsar el encoder)
  subir foco    (girar el encoder a la derecha)
  bajar fuerza  (Strength)
  subir fuerza  (Strength)

Las teclas y los modificadores viven en las preferencias (propiedades normales,
que Blender guarda como cualquier otra pref). El maestro `enable_hotkeys` los
enciende o apaga; cambiar cualquier tecla reconstruye los atajos al vuelo.
"""

import bpy

from . import utils

# Pares (keymap, keymap_item) creados por el addon, para limpiarlos en unregister().
addon_keymaps = []


def register_keymaps():
    """Crea los cinco atajos leyendo teclas y modificadores de las preferencias."""
    prefs = utils.get_prefs(bpy.context)
    if prefs is None or not prefs.enable_hotkeys:
        return

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc is None:  # modo background: no hay keyconfig de addon
        return

    km = kc.keymaps.new(name="Sculpt", space_type='EMPTY')

    def mods(prop):
        """Modificadores propios de esa tecla, leídos de las preferencias."""
        return {
            "ctrl": getattr(prefs, prop + "_ctrl"),
            "alt": getattr(prefs, prop + "_alt"),
            "shift": getattr(prefs, prop + "_shift"),
        }

    kmi = km.keymap_items.new(
        "sculpt_ext.focus_adjust", prefs.key_down, 'PRESS', **mods("key_down"))
    kmi.properties.direction = -1  # bajar foco
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new(
        "sculpt_ext.focus_ring_toggle", prefs.key_toggle, 'PRESS',
        **mods("key_toggle"))
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new(
        "sculpt_ext.focus_adjust", prefs.key_up, 'PRESS', **mods("key_up"))
    kmi.properties.direction = 1  # subir foco
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new(
        "sculpt_ext.strength_adjust", prefs.strength_key_down, 'PRESS',
        **mods("strength_key_down"))
    kmi.properties.direction = -1  # bajar fuerza
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new(
        "sculpt_ext.strength_adjust", prefs.strength_key_up, 'PRESS',
        **mods("strength_key_up"))
    kmi.properties.direction = 1  # subir fuerza
    addon_keymaps.append((km, kmi))


def unregister_keymaps():
    """Elimina todos los atajos creados por el addon."""
    for km, kmi in addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except (RuntimeError, ReferenceError):
            pass
    addon_keymaps.clear()


def rebuild_keymaps():
    """Rehace los atajos desde cero: usado tras cambiar una tecla en preferencias."""
    unregister_keymaps()
    prefs = utils.get_prefs(bpy.context)
    if prefs is not None and prefs.enable_hotkeys:
        register_keymaps()


def register():
    register_keymaps()


def unregister():
    unregister_keymaps()
