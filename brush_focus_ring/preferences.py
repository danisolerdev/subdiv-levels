"""Preferencias del addon: colores, grosor, comportamiento y atajos."""

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
)


def _event_type_items():
    """Lista de teclas disponibles para los desplegables de atajos."""
    items = []
    seen = set()
    for it in bpy.types.KeyMapItem.bl_rna.properties["type"].enum_items:
        if it.identifier in seen:
            continue
        seen.add(it.identifier)
        items.append((it.identifier, it.name, ""))
    return items


# Se calcula una vez al importar el módulo (bpy ya está disponible al registrar).
_EVENT_TYPE_ITEMS = _event_type_items()

# Nombre legible de cada tecla (p. ej. 'GRLESS' -> "Grless") para el texto del combo.
_EVENT_TYPE_NAMES = {ident: name for ident, name, _ in _EVENT_TYPE_ITEMS}

# Las cinco acciones con atajo y su etiqueta (msgid en inglés, se traduce en la UI).
_KEY_ACTIONS = (
    ("key_down", "Lower Focus"),
    ("key_toggle", "Toggle Ring"),
    ("key_up", "Raise Focus"),
    ("strength_key_down", "Lower Strength"),
    ("strength_key_up", "Raise Strength"),
)


def _rebuild_keymaps(self, context):
    """Reconstruye los atajos al cambiar la casilla maestra o cualquier tecla."""
    from . import keymaps  # import perezoso: evita import circular en carga
    keymaps.rebuild_keymaps()


class BrushFocusRingPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    outer_color: FloatVectorProperty(
        name="Outer Color (influence)",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 0.35, 0.1, 0.9),
    )
    inner_color: FloatVectorProperty(
        name="Inner Color (focus)",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.9),
    )
    line_width: FloatProperty(
        name="Line Width",
        min=1.0,
        max=5.0,
        default=1.5,
    )
    min_inner_ratio: FloatProperty(
        name="Minimum Inner Radius",
        description="Fraction of the outer radius still visible when the focus is 0",
        min=0.0,
        max=0.5,
        default=0.05,
    )
    hide_native_cursor: BoolProperty(
        name="Hide Native Cursor in Sculpt",
        description="Disables Blender's circle while the ring is active",
        default=True,
    )
    enable_hotkeys: BoolProperty(
        name="Enable Encoder Hotkeys",
        description=(
            "Registers the three focus encoder keys in Sculpt mode. "
            "Change each key in the dropdowns below"
        ),
        default=True,
        update=_rebuild_keymaps,
    )
    # Cada tecla lleva sus propios modificadores (Ctrl/Alt/Shift), así una puede
    # ir suelta y otra con combinación. Se capturan juntos con el cuentagotas.
    key_down: EnumProperty(
        name="Lower Focus",
        description="Key to lower the focus (turn the encoder left)",
        items=_EVENT_TYPE_ITEMS,
        default='Z',
        update=_rebuild_keymaps,
    )
    key_down_ctrl: BoolProperty(name="Ctrl", default=True, update=_rebuild_keymaps)
    key_down_alt: BoolProperty(name="Alt", default=True, update=_rebuild_keymaps)
    key_down_shift: BoolProperty(name="Shift", default=True, update=_rebuild_keymaps)
    key_toggle: EnumProperty(
        name="Toggle Ring",
        description="Key to turn the ring on or off (press the encoder)",
        items=_EVENT_TYPE_ITEMS,
        default='X',
        update=_rebuild_keymaps,
    )
    key_toggle_ctrl: BoolProperty(name="Ctrl", default=True, update=_rebuild_keymaps)
    key_toggle_alt: BoolProperty(name="Alt", default=True, update=_rebuild_keymaps)
    key_toggle_shift: BoolProperty(name="Shift", default=True, update=_rebuild_keymaps)
    key_up: EnumProperty(
        name="Raise Focus",
        description="Key to raise the focus (turn the encoder right)",
        items=_EVENT_TYPE_ITEMS,
        default='C',
        update=_rebuild_keymaps,
    )
    key_up_ctrl: BoolProperty(name="Ctrl", default=True, update=_rebuild_keymaps)
    key_up_alt: BoolProperty(name="Alt", default=True, update=_rebuild_keymaps)
    key_up_shift: BoolProperty(name="Shift", default=True, update=_rebuild_keymaps)
    focus_step: FloatProperty(
        name="Focus Step",
        description="How much the focus changes with each encoder notch",
        min=0.01,
        max=0.5,
        default=0.05,
    )
    # Dos teclas más, para la fuerza (Strength), con sus propios modificadores.
    strength_key_down: EnumProperty(
        name="Lower Strength",
        description="Key to lower the strength (turn the encoder left)",
        items=_EVENT_TYPE_ITEMS,
        default='V',
        update=_rebuild_keymaps,
    )
    strength_key_down_ctrl: BoolProperty(name="Ctrl", default=True, update=_rebuild_keymaps)
    strength_key_down_alt: BoolProperty(name="Alt", default=True, update=_rebuild_keymaps)
    strength_key_down_shift: BoolProperty(name="Shift", default=True, update=_rebuild_keymaps)
    strength_key_up: EnumProperty(
        name="Raise Strength",
        description="Key to raise the strength (turn the encoder right)",
        items=_EVENT_TYPE_ITEMS,
        default='B',
        update=_rebuild_keymaps,
    )
    strength_key_up_ctrl: BoolProperty(name="Ctrl", default=True, update=_rebuild_keymaps)
    strength_key_up_alt: BoolProperty(name="Alt", default=True, update=_rebuild_keymaps)
    strength_key_up_shift: BoolProperty(name="Shift", default=True, update=_rebuild_keymaps)

    def draw(self, context):
        col = self.layout.column()
        col.prop(self, "outer_color")
        col.prop(self, "inner_color")
        col.prop(self, "line_width")
        col.prop(self, "min_inner_ratio")
        col.prop(self, "hide_native_cursor")

        col.separator()
        col.label(text="Focus encoder hotkeys (Sculpt mode):")
        col.prop(self, "enable_hotkeys")
        if self.enable_hotkeys:
            col.prop(self, "focus_step")
            self._draw_keymaps(context, col)

    def _draw_keymaps(self, context, layout):
        """Cada acción en su caja: combinación visible arriba, edición debajo."""
        for prop, label in _KEY_ACTIONS:
            self._key_row(layout, prop, label)

    def _combo_text(self, prop) -> str:
        """Texto de la combinación de una tecla, p. ej. 'Ctrl + C'."""
        parts = []
        if getattr(self, prop + "_ctrl"):
            parts.append("Ctrl")
        if getattr(self, prop + "_alt"):
            parts.append("Alt")
        if getattr(self, prop + "_shift"):
            parts.append("Shift")
        key_id = getattr(self, prop)
        parts.append(_EVENT_TYPE_NAMES.get(key_id, key_id))
        return " + ".join(parts)

    def _key_row(self, layout, prop, label):
        """Caja de una acción: nombre + combinación clara, y controles para editarla."""
        box = layout.box()
        header = box.row()
        header.label(text=label)
        combo = header.row()
        combo.alignment = 'RIGHT'
        combo.label(text=self._combo_text(prop))

        edit = box.row(align=True)
        edit.prop(self, prop + "_ctrl", toggle=True)
        edit.prop(self, prop + "_alt", toggle=True)
        edit.prop(self, prop + "_shift", toggle=True)
        edit.prop(self, prop, text="")
        op = edit.operator("sculpt_ext.capture_key", text="", icon='EYEDROPPER')
        op.target = prop


classes = (BrushFocusRingPreferences,)
