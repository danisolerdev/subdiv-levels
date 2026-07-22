"""Helpers compartidos: Tool root, recorrido del árbol de colecciones y prefs."""

import bpy


class _FallbackPrefs:
    """Valores por defecto cuando las preferencias del addon no están disponibles
    (p. ej. al registrar el paquete a mano en un smoke test)."""

    switch_reenters_sculpt = True
    solo_includes_group = False
    confirm_delete = True
    confirm_merge = True
    enable_hotkeys = False
    sort_mode = 'MANUAL'
    show_thumbnails = True
    auto_thumbnails = True
    thumbnail_scale = 3.0


_fallback_prefs = _FallbackPrefs()


def get_prefs():
    """Devuelve las preferencias del addon, o valores por defecto si no existen."""
    addon = bpy.context.preferences.addons.get(__package__)
    if addon is not None and addon.preferences is not None:
        return addon.preferences
    return _fallback_prefs


def prefs_are_real(prefs) -> bool:
    """True si `prefs` es un AddonPreferences real (dibujable en la UI)."""
    return isinstance(prefs, bpy.types.AddonPreferences)


def is_subtool(obj) -> bool:
    """True si el objeto puede tratarse como subtool (malla)."""
    return obj is not None and obj.type == 'MESH'


def _collection_parent(root, target):
    """Busca la colección padre de `target` recorriendo el árbol desde `root`."""
    for child in root.children:
        if child == target:
            return root
        found = _collection_parent(child, target)
        if found is not None:
            return found
    return None


def get_tool_root(obj):
    """Colección "Tool" del objeto: el ancestro más externo bajo la Scene Collection.

    Se sube desde la colección directa del objeto hasta la colección cuyo padre es
    la Scene Collection. Si el objeto solo está en la Scene Collection, esa es el Tool.
    """
    scene_coll = bpy.context.scene.collection
    cols = list(obj.users_collection) if obj is not None else []
    if not cols:
        return scene_coll
    current = cols[0]
    while True:
        parent = _collection_parent(scene_coll, current)
        if parent is None or parent == scene_coll:
            return current
        current = parent


def subtools_of(coll, sort_mode='MANUAL'):
    """Objetos malla directos de `coll`, ordenados según `sort_mode`."""
    objs = [o for o in coll.objects if o.type == 'MESH']
    if sort_mode == 'NAME':
        objs.sort(key=lambda o: o.name.lower())
    else:
        objs.sort(key=lambda o: (o.subtool_order, o.name.lower()))
    return objs


def child_groups(coll):
    """Sub-colecciones (grupos) de `coll`."""
    return list(coll.children)


def all_subtools(coll, sort_mode='MANUAL'):
    """Aplana el árbol: objetos del nivel y luego los de cada grupo, en orden de dibujo."""
    result = list(subtools_of(coll, sort_mode))
    for child in child_groups(coll):
        result.extend(all_subtools(child, sort_mode))
    return result
