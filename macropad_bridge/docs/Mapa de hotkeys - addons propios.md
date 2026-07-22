# Mapa de hotkeys — addons propios

Referencia para configurar el macropad (12 teclas + 4 encoders con pulsación)
con los operadores de `subdiv_levels`, `brush_focus_ring`, `sculpt_subtools`
y `macropad_bridge`.

Principio: **el macropad solo envía teclas F13–F24** (con modificadores si hace
falta). Blender no usa ninguna de ellas por defecto, así que hay cero colisiones
con el keymap nativo y con los atajos `Ctrl/Shift/Alt+D` de `subdiv_levels`.

---

## 1. Ya configurado (no tocar)

`macropad_bridge` v0.1.0 registra estos atajos al activarse:

| Encoder | CW | CCW | Operador |
|---|---|---|---|
| 1 · Tamaño de pincel | `F13` | `F14` | `macropad.brush_size` (×1.15 por muesca) |
| 2 · Nivel de subdivisión | `F15` | `F16` | `sculpt_ext.level_up` / `level_down` |
| 3 · Foco (dureza) | `F17` | `F18` | `macropad.focus` (±0.05) |
| 4 · Deshacer / Rehacer | `F19` | `F20` | `ed.redo` / `ed.undo` |

Keymap: los tres primeros en **Sculpt**, undo/redo en **Window**.

---

## 2. Pulsaciones de encoder → F21–F24

Cada pulsación hace la acción "hermana" de lo que gira ese encoder. Ninguno de
estos operadores necesita argumentos, así que se asignan directamente.

| Tecla | Encoder | Operador | Qué hace |
|---|---|---|---|
| `F21` | E1 (tamaño) | `sculpt_ext.subtool_frame_active` | Encuadra la vista en el subtool activo |
| `F22` | E2 (subdiv) | `sculpt_ext.subdiv_smart` | El Ctrl+D inteligente: crea Multires o añade nivel |
| `F23` | E3 (foco) | `sculpt_ext.focus_ring_toggle` | Enciende/apaga el anillo de foco |
| `F24` | E4 (undo) | `sculpt_ext.subtool_show_all` | Botón de pánico: muestra todo y quita el Solo |

---

## 3. Teclas de la paleta → F13–F20 con modificador

Para las 12 teclas del macropad. Todos estos operadores funcionan sin
argumentos (actúan sobre el subtool activo), salvo donde se indica.

**Shift + F13–F20 — subtools:**

| Tecla | Operador | Acción | Prioridad |
|---|---|---|---|
| `Shift+F13` | `sculpt_ext.subtool_cycle` · `direction='PREV'` | Subtool anterior | ★★★ |
| `Shift+F14` | `sculpt_ext.subtool_cycle` · `direction='NEXT'` | Subtool siguiente | ★★★ |
| `Shift+F15` | `sculpt_ext.subtool_split_mask` | Separar zona enmascarada a subtool nuevo | ★★★ |
| `Shift+F16` | `sculpt_ext.subtool_split_faceset` | Separar por Face Sets | ★★ |
| `Shift+F17` | `sculpt_ext.subtool_duplicate` | Duplicar subtool activo | ★★ |
| `Shift+F18` | `sculpt_ext.subtool_delete` | Borrar subtool activo | ★ |
| `Shift+F19` | `sculpt_ext.subtool_merge` | Unir seleccionados en el activo | ★★ |
| `Shift+F20` | `sculpt_ext.subtool_split_loose` | Separar por partes sueltas | ★ |

**Ctrl + F13–F20 — booleanas, espejo y multires:**

| Tecla | Operador | Acción | Prioridad |
|---|---|---|---|
| `Ctrl+F13` | `sculpt_ext.subtool_mirror` · `axis='X'` | Copia reflejada en X | ★★★ |
| `Ctrl+F14` | `sculpt_ext.subtool_bool_preview` | Preview booleano en vivo (toggle) | ★★ |
| `Ctrl+F15` | `sculpt_ext.subtool_bool_apply` | Hornear la booleana | ★★ |
| `Ctrl+F16` | `sculpt_ext.subtool_bool_direct` · `op='DIFFERENCE'` | Booleana directa: restar | ★★ |
| `Ctrl+F17` | `sculpt_ext.subtool_bool_direct` · `op='UNION'` | Booleana directa: unir | ★ |
| `Ctrl+F18` | `sculpt_ext.subtool_multires_step` · `delta=1` | Subir Multires solo del subtool activo | ★ |
| `Ctrl+F19` | `sculpt_ext.subtool_multires_step` · `delta=-1` | Bajar Multires solo del subtool activo | ★ |
| `Ctrl+F20` | `sculpt_ext.delete_higher` | Borrar niveles superiores (pide confirmación) | ★ |

`sculpt_ext.apply_base` y `sculpt_ext.apply_modifier` se dejan fuera a propósito:
son destructivos y con confirmación, mejor desde el panel.

---

## 4. Operadores que NO se pueden asignar tal cual

Tres operadores muy usables desde macropad reciben un `name`/`target` de tipo
StringProperty y buscan el objeto con `bpy.data.objects.get(self.name)`. Desde
un keymap ese campo llega vacío y el operador devuelve `CANCELLED` sin avisar:

| Operador | Propiedad requerida |
|---|---|
| `sculpt_ext.subtool_solo` | `name` |
| `sculpt_ext.subtool_toggle_visible` | `name` |
| `sculpt_ext.subtool_bool_cycle_op` | `target` |

**Arreglo (fase 2, ~3 líneas por operador):** que un `name` vacío signifique
"objeto activo". En cada `execute()`:

```python
obj = bpy.data.objects.get(self.name) if self.name else context.object
if obj is None:
    return {'CANCELLED'}
```

Con eso, `Solo` (aislar el subtool activo) pasa a ser asignable y es el atajo
más rentable de todo el addon. Reserva `Shift+F21` para él.

---

## 5. Cómo asignar cada tecla en Blender

Estos atajos no los registra ningún addon: se crean a mano una vez.

1. `Edit → Preferences → Keymap`.
2. Despliega **3D View → Sculpt** (o **Window** para los globales).
3. `Add New` al final de la lista.
4. En la entrada nueva, sustituye `none` por el `bl_idname` de la tabla
   (por ejemplo `sculpt_ext.subtool_split_mask`).
5. Click en el campo de tecla y pulsa la tecla del macropad. Marca `Shift` o
   `Ctrl` si corresponde.
6. Si el operador tiene propiedad (`direction`, `axis`, `op`, `delta`),
   despliega la entrada y rellénala. **Este paso es el que más se olvida**: sin
   él, `subtool_cycle` siempre irá en la misma dirección.

Para guardarlo: `Preferences → ⌄ → Save Preferences`, o exporta el keymap desde
`Keymap → Export` para tener copia.

---

## 6. Colisiones a vigilar

- `Ctrl+D` en Sculpt es Dyntopo en Blender nativo; `subdiv_levels` lo pisa. Si
  quieres Dyntopo, reasígnalo a `Ctrl+Alt+D`.
- `Alt+Up` / `Alt+Down` de `sculpt_subtools` vienen **desactivados** por defecto
  (`enable_hotkeys`). Si activas las preferencias del addon *y* asignas
  `Shift+F13/F14` a lo mismo, tendrás dos rutas al mismo operador: no rompe
  nada, pero conviene dejar una sola.
- Los cuatro encoders están ocupados. Si añades un quinto, el mejor candidato
  para encoder es `subtool_cycle` PREV/NEXT: recorrer subtools con la rueda es
  exactamente el gesto de ZBrush.

---

## 7. Detalle: Brush Focus Ring

El addon expone **un solo operador** (`sculpt_ext.focus_ring_toggle`) y una
propiedad de escena (`bfr_focus`). Aun así se pueden sacar 5 teclas útiles sin
escribir código nuevo, usando los operadores genéricos `wm.context_set_float` y
`wm.context_toggle`.

| Tecla | Operador | data_path / valor | Acción |
|---|---|---|---|
| `F23` (E3 push) | `sculpt_ext.focus_ring_toggle` | — | Encender/apagar el anillo |
| `F17` / `F18` | `macropad.focus` | — | Foco ±0.05 (ya registrado, encoder 3) |
| `Shift+F17` | `wm.context_set_float` | `scene.bfr_focus` → `0.0` | Foco mínimo: caída total, trazo suave |
| `Shift+F18` | `wm.context_set_float` | `scene.bfr_focus` → `1.0` | Foco pleno: borde duro, tipo sello |
| `Ctrl+F17` | `wm.context_set_float` | `scene.bfr_focus` → `0.5` | Reset al valor por defecto |
| `Ctrl+F18` | `wm.context_toggle` | `tool_settings.sculpt.show_brush` | Mostrar/ocultar el círculo nativo |

### Por qué presets absolutos y no relativos

`bfr_focus` vive en la escena, pero el valor real que esculpe es
`brush.hardness` de cada pincel. Al cambiar de pincel, `bfr_focus` **no se
resincroniza** (solo se escribe hacia el pincel, nunca al revés): el slider
puede marcar 0.5 mientras el pincel activo tiene 0.9.

Un `wm.context_set_float` fuerza el valor absoluto y dispara el callback
`_on_focus_update`, que lo escribe en el pincel y redibuja. Es decir: los
presets **corrigen** el desfase, mientras que un paso relativo lo arrastra.
Por eso las tres teclas de preset valen más que otro par de ± .

### Ojo con `hide_native_cursor`

La preferencia `hide_native_cursor` solo se lee en el `invoke()` del modal
(`_maybe_hide_native_cursor`). Mapearla con `wm.context_toggle` sobre
`preferences.addons["brush_focus_ring"].preferences.hide_native_cursor`
**no hace nada hasta reiniciar el anillo**. Por eso la tabla usa
`tool_settings.sculpt.show_brush`, que sí responde al instante.

### Qué haría falta para más teclas

Con el addon tal cual, lo de arriba agota su superficie. Si en algún momento
quieres más, los candidatos serían un operador `sculpt_ext.focus_preset` con
`value: FloatProperty` (una sola entrada de keymap parametrizable, en vez de
tres `wm.context_set_float`) y un ciclador de colores del anillo.
