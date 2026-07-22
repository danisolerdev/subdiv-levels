# Macropad Bridge — Guía de instalación y mapeo

Addon-puente que conecta los 4 encoders de un macropad con acciones de Sculpt
en Blender 5.x. Los encoders solo envían teclas: este addon traduce **F13–F20**
a las acciones reales.

## Requisitos

- Blender 5.x.
- **`subdiv_levels`** instalado y activado (el Encoder 2 usa sus operadores
  `sculpt_ext.level_up` / `sculpt_ext.level_down`).
- Opcional pero recomendado: **`brush_focus_ring`** activado. Si está, el
  Encoder 3 mueve la propiedad `bfr_focus` y el anillo se actualiza en vivo.
  Si no está, el foco escribe directamente en `brush.hardness`.

## Instalación

1. Blender → Edit → Preferences → Get Extensions → Install from Disk.
2. Elige `dist/macropad_bridge-0.1.0.zip`.
3. Actívalo. En sus preferencias puedes cambiar el paso del tamaño (`size_factor`)
   y del foco (`focus_step`), o desactivar los atajos.

## Mapa de encoders

| Encoder | Giro derecha (CW) | Giro izquierda (CCW) | Acción |
|---|---|---|---|
| 1 · Tamaño de pincel | **F13** | **F14** | `macropad.brush_size` (multiplicativo) |
| 2 · Subdivisión | **F15** | **F16** | `sculpt_ext.level_up` / `level_down` |
| 3 · Foco | **F17** | **F18** | `macropad.focus` (dureza ±) |
| 4 · Deshacer/Rehacer | **F19** (rehacer) | **F20** (deshacer) | `ed.redo` / `ed.undo` |

Se eligió F13–F20 porque Blender no los usa por defecto: cero colisiones con los
atajos nativos ni con tus otros addons (que usan Ctrl/Shift/Alt+D).

## Configurar el macropad

El principio es el mismo en cualquier software: **cada sentido de giro de cada
encoder debe enviar una de las teclas F13–F20** de la tabla. Pasos generales:

1. Abre la app de tu macropad y selecciona la capa/perfil que uses con Blender.
2. Para cada encoder, edita la acción de "girar a la derecha" y "girar a la
   izquierda" (a veces llamadas Rotate CW / CCW o Encoder Right / Left).
3. Asigna la tecla correspondiente de la tabla como pulsación simple (no macro).
4. Guarda o sincroniza el perfil al dispositivo.

Notas por tipo de software:

- **VIA / VIAL (QMK):** pestaña de encoders o la matriz de teclas. Los F13–F24
  están en la categoría "Special" / "Function". Asigna KC_F13…KC_F20.
- **App del fabricante (Ajazz, YMDK, Epomaker, etc.):** busca "Encoder" o el icono
  de la rueda; cada dirección es una fila. Selecciona la tecla del teclado F13–F20.
  Si la lista solo llega a F12, usa la alternativa de abajo.
- **Elgato Stream Deck +:** en el dial, acción "Hotkey" del plugin de teclado.

### Si tu software no llega a F13–F20

Algunas apps solo permiten hasta F12. En ese caso cambia los atajos del addon a
combinaciones que sí puedas enviar (p. ej. `Ctrl+Alt+1…8`):

Blender → Preferences → Keymap → filtra por `macropad` y también por
`sculpt_ext.level` → edita cada entrada con la tecla que emita tu macropad.
Recuerda evitar `Ctrl+D`, `Shift+D`, `Alt+D` (ya usados por subdiv_levels).

## Prueba rápida

1. Entra en modo Sculpt con una malla.
2. Encoder 1: el círculo del pincel debe crecer/encoger.
3. Encoder 2: sube/baja niveles (necesita un Multires; `Ctrl+D` lo crea).
4. Encoder 3: cambia el foco (dureza); con brush_focus_ring, el anillo interior
   se mueve.
5. Encoder 4: deshace y rehace trazos.

Si un encoder no responde, comprueba en Preferences → Keymap (filtro `macropad`)
que la entrada existe y que la tecla coincide con la que envía el dispositivo.
