"""Registro y limpieza de los atajos que enlazan los encoders.

Se usan combinaciones Ctrl+Alt+Shift + letra. Con letras, Shift solo hace
mayuscula (nunca un simbolo raro como pasa con los numeros), asi la app del
macropad captura una tecla inequivoca. Blender no usa estas combinaciones por
defecto, asi que no colisionan con nada.

Las letras van en columnas del teclado (arriba sube, abajo baja):

Encoder 1 - Tamano   : Ctrl+Alt+Shift+Q subir / +A bajar    -> macropad.brush_size
Encoder 2 - Subdiv   : Ctrl+Alt+Shift+W subir / +S bajar    -> sculpt_ext.level_up / _down
Encoder 3 - Foco     : Ctrl+Alt+Shift+E subir / +D bajar    -> macropad.focus
Encoder 4 - Undo/Redo: Ctrl+Alt+Shift+R rehacer / +F deshacer -> ed.redo / ed.undo

Tamano, subdivision y foco se registran en el keymap "Sculpt". Deshacer y
rehacer van en "Window" para funcionar en cualquier contexto.
"""

import bpy

from . import utils

# Pares (keymap, keymap_item) creados por el addon, para limpiarlos en unregister().
addon_keymaps = []

# Modificador comun a todos los atajos: Ctrl+Alt+Shift.
_MODS = {"ctrl": True, "alt": True, "shift": True}


def _new(km, idname, key, props=None):
    """Crea un keymap_item con Ctrl+Alt+Shift y opcionalmente fija propiedades."""
    kmi = km.keymap_items.new(idname, key, 'PRESS', **_MODS)
    if props:
        for name, value in props.items():
            setattr(kmi.properties, name, value)
    addon_keymaps.append((km, kmi))


def register_keymaps():
    """Crea los atajos si estan habilitados en las preferencias."""
    prefs = utils.get_prefs(bpy.context)
    if not prefs.enable_hotkeys:
        return

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc is None:  # modo background: no hay keyconfig de addon
        return

    km_sculpt = kc.keymaps.new(name="Sculpt", space_type='EMPTY')
    _new(km_sculpt, "macropad.brush_size", 'Q', {"up": True})
    _new(km_sculpt, "macropad.brush_size", 'A', {"up": False})
    _new(km_sculpt, "sculpt_ext.level_up", 'W')
    _new(km_sculpt, "sculpt_ext.level_down", 'S')
    _new(km_sculpt, "macropad.focus", 'E', {"up": True})
    _new(km_sculpt, "macropad.focus", 'D', {"up": False})

    km_window = kc.keymaps.new(name="Window", space_type='EMPTY')
    _new(km_window, "ed.redo", 'R')
    _new(km_window, "ed.undo", 'F')


def unregister_keymaps():
    """Elimina todos los atajos creados por el addon."""
    for km, kmi in addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except (RuntimeError, ReferenceError):
            pass
    addon_keymaps.clear()


def register():
    register_keymaps()


def unregister():
    unregister_keymaps()
