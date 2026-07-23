# Brush Focus Ring — Addon para Blender

> Doble circunferencia de pincel estilo ZBrush: **foco** (dureza) e **influencia** (tamaño).
> Versión **0.7.4** · Blender **5.0+** · Licencia GPL-3.0-or-later

---

## ¿Qué hace?

Dibuja alrededor del cursor de esculpido **dos circunferencias**: la exterior marca la
influencia real del pincel (su tamaño/Size) y la interior marca el **foco**, es decir, la
zona de máxima intensidad. Es la lectura visual que ZBrush da de serie y que Blender no
ofrece: de un vistazo sabes hasta dónde llega el pincel y cómo de concentrada está su fuerza.

El foco se controla con un valor de 0 a 1 (`bfr_focus`) mapeado sobre el radio del pincel.
El addon añade además atajos pensados para un **encoder de macropad**, que permiten subir y
bajar el foco y la fuerza girando una rueda, sin soltar la tableta.

---

## Instalación

1. Localiza el zip: `dist/brush_focus_ring-0.7.4.zip`.
2. En Blender: **Edit → Preferences → Get Extensions**.
3. Flecha desplegable (esquina superior derecha) → **Install from Disk…**
4. Selecciona el zip. Se instala y activa automáticamente.

Para actualizar tras un cambio de código, reconstruye el zip y repite *Install from Disk*
(Blender lo actualiza sin desinstalar):

```
python build_addons.py brush_focus_ring
```

---

## Uso básico

1. Entra en modo **Sculpt** (o Vertex/Weight/Texture Paint).
2. En la cabecera del viewport, junto a *Size* y *Strength*, aparece un slider **Focus**.
   También lo tienes en el panel lateral (`N`) → pestaña **Focus**.
3. Pulsa **Enable Ring** (o el atajo de toggle) para que se dibuje el anillo doble.
4. Ajusta *Focus* para abrir o cerrar la circunferencia interior. Con *Focus* bajo el pincel
   pega fino y concentrado; con *Focus* alto, la zona de máxima fuerza casi llena el radio.

Mientras el anillo está activo se puede ocultar el cursor nativo de Blender (opción en
preferencias) para no tener dos círculos superpuestos.

---

## Panel

Viewport 3D → barra lateral (`N`) → pestaña **Focus**:

- **Enable / Disable Ring**: activa o apaga el dibujo del anillo.
- **Influence (Size)** y **Focus** en píxeles: lectura en vivo de ambos radios.
- Slider **Focus**: el mismo valor `bfr_focus` que la cabecera.

Si no hay pincel activo, el panel lo indica y no muestra los radios.

---

## Atajos (encoder de macropad)

El addon registra en el keymap de **Sculpt** cinco acciones, pensadas para un encoder con
pulsador (girar = subir/bajar, pulsar = toggle). Cada acción tiene **su propia tecla y sus
propios modificadores** (Ctrl/Alt/Shift), configurables en las preferencias.

| Acción | Tecla por defecto | Qué hace |
|---|---|---|
| Lower Focus | `Z` | Baja el foco un paso |
| Toggle Ring | `X` | Enciende / apaga el anillo |
| Raise Focus | `C` | Sube el foco un paso |
| Lower Strength | `V` | Baja la fuerza (Strength) del pincel |
| Raise Strength | `B` | Sube la fuerza del pincel |

> Por defecto las cinco llevan **Ctrl+Alt+Shift** como modificador, para no chocar con los
> atajos nativos de Sculpt. Un macropad puede enviar esa combinación junto a cada tecla.

### Configurar cada atajo

En **Preferences → Add-ons → Brush Focus Ring → Focus encoder hotkeys**, cada acción tiene su
propia caja que muestra la combinación completa (por ejemplo `Ctrl + C`) y, debajo:

- Tres botones **Ctrl / Alt / Shift** para activar o quitar modificadores de *esa* tecla.
- Un desplegable con la tecla.
- Un botón **cuentagotas** (💧): púlsalo y presiona la combinación que quieras; captura
  tecla y modificadores de golpe.

Como los modificadores son **independientes por tecla**, puedes tener una acción con
combinación (`Ctrl+C`) y otra suelta (por ejemplo `<` sin nada) a la vez.

> Teclado español (ISO): la tecla `<` Blender la llama internamente **Grless**. Si la
> asignas desde el desplegable, busca *Grless*; si usas el cuentagotas, basta con pulsar `<`.

Todo el sistema de atajos se puede desactivar con la casilla **Enable Encoder Hotkeys**.

---

## Preferencias

En **Preferences → Add-ons → Brush Focus Ring**:

| Opción | Por defecto | Descripción |
|---|---|---|
| Outer Color (influence) | naranja | Color de la circunferencia exterior (tamaño) |
| Inner Color (focus) | blanco | Color de la circunferencia interior (foco) |
| Line Width | 1.5 | Grosor de línea de las circunferencias |
| Minimum Inner Radius | 0.05 | Fracción del radio exterior visible aunque el foco sea 0 |
| Hide Native Cursor in Sculpt | ✅ | Oculta el círculo de Blender mientras el anillo está activo |
| Enable Encoder Hotkeys | ✅ | Registra/quita los cinco atajos al vuelo |
| Focus Step | 0.05 | Cuánto cambia el foco/fuerza en cada muesca del encoder |

Cambiar cualquier tecla o modificador reconstruye los atajos al instante, sin reiniciar.

---

## Estructura del código

```
brush_focus_ring/
├── blender_manifest.toml   # metadatos de la extensión (formato Blender 4.2+)
├── __init__.py             # register()/unregister()
├── draw.py                 # dibujo GPU del anillo doble
├── operators.py            # toggle, ajuste de foco/fuerza, captura de tecla
├── ui.py                   # panel lateral + slider de cabecera
├── keymaps.py              # atajos (reconstruidos desde preferencias)
├── preferences.py          # AddonPreferences (colores, atajos por tecla)
├── translations.py         # traducciones (es, fr, de, zh, ja, ko, pt, it)
└── utils.py                # estado, radios, aplicar foco al pincel
```

### Operadores

| bl_idname | Función |
|---|---|
| `sculpt_ext.focus_ring_toggle` | Enciende/apaga el anillo (operador modal que sigue el ratón) |
| `sculpt_ext.focus_adjust` | Sube o baja el foco un paso (`direction: int`) |
| `sculpt_ext.strength_adjust` | Sube o baja la fuerza del pincel un paso (`direction: int`) |
| `sculpt_ext.capture_key` | Captura una combinación de teclas para un atajo (`target: str`) |

---

## Compatibilidad e idiomas

- Blender **5.0+** (desarrollado sobre 5.1.2).
- Interfaz traducida a español, francés, alemán, chino simplificado, japonés, coreano,
  portugués e italiano; Blender elige según el idioma de la preferencia.

---

## Historial

| Versión | Cambios |
|---|---|
| 0.7.4 | Modificadores independientes por tecla; cada casilla muestra la combinación (`Ctrl + C`) |
| 0.7.x | Atajos de encoder para foco y fuerza; slider en cabecera; traducciones |
