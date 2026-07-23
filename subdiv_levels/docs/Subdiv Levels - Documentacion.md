# Subdiv Levels — Addon para Blender

> Niveles de subdivisión estilo ZBrush / Nomad Sculpt para el modo Sculpt de Blender.
> Versión **0.3.0** · Blender **5.0+** · Licencia GPL-3.0-or-later

---

## ¿Qué hace?

Replica el flujo de trabajo de niveles de subdivisión de ZBrush y Nomad Sculpt sobre el modificador **Multiresolution** de Blender: subir y bajar de nivel con atajos, añadir niveles nuevos y borrar los superiores, todo sin salir del modo Sculpt.

El addon **no reimplementa la subdivisión**: orquesta el modificador Multires nativo con una UX rápida (atajos + panel), que es lo que Blender no ofrece de serie.

---

## Instalación

1. Localiza el zip: `dist\subdiv_levels-0.3.0.zip` (dentro de la carpeta del proyecto `addonBlender`).
2. En Blender: **Edit → Preferences → Get Extensions**.
3. Flecha desplegable (esquina superior derecha) → **Install from Disk…**
4. Selecciona el zip. Se instala y activa automáticamente.

Para actualizar tras un cambio de código: reconstruir el zip y repetir *Install from Disk* (Blender lo actualiza sin desinstalar).

```
blender --command extension build --source-dir subdiv_levels --output-dir dist
```

---

## Atajos de teclado

| Atajo | Acción | Modos |
|---|---|---|
| `Ctrl+D` | Subdividir inteligente | Sculpt y Objeto |
| `Shift+D` | Bajar un nivel | Solo Sculpt |
| `Alt+D` | Subir un nivel (sin crear) | Solo Sculpt |

- `Shift+D` y `Alt+D` no se registran en modo Objeto para no pisar *Duplicar*.
- Los atajos se pueden desactivar en las preferencias del addon.

### Lógica del Ctrl+D inteligente

1. **Sin modificador Multires** → lo crea y sube a nivel 1 en un solo gesto.
2. **En un nivel intermedio** → sube un nivel (no crea nada).
3. **En el nivel máximo** → añade un nivel nuevo (Catmull-Clark por defecto).
4. **Límite de seguridad**: no crea niveles nuevos por encima de `max_auto_level` (7 por defecto); avisa en su lugar.

---

## Panel

En el Viewport 3D, barra lateral (`N`) → pestaña **Subdiv**. Visible en modo Objeto y Sculpt.

- **Sin multires**: botón grande *Añadir Multires*.
- **Nivel actual**: `Nivel 3 / 5` con botones `−` / `+`.
- **Botón principal**: *Subdividir (Ctrl+D)*.
- **Avanzado** (plegable):
  - *Borrar niveles superiores* (pide confirmación) — elimina el detalle por encima del nivel actual.
  - *Aplicar base* (pide confirmación) — aplica el desplazamiento a la malla base.
  - Selector de modo de subdivisión.
  - Sliders nativos de nivel de viewport y render.
- **Pie**: recuento aproximado de caras del nivel activo (caras base × 4^nivel).

---

## Preferencias

En **Preferences → Add-ons → Subdiv Levels**:

| Opción | Por defecto | Descripción |
|---|---|---|
| Modo de subdivisión | Catmull-Clark | Algoritmo al crear niveles (Catmull-Clark / Simple / Lineal) |
| Nivel máximo automático | 7 | Techo de seguridad para Ctrl+D |
| Sincronizar viewport | ✅ | Al cambiar de nivel, actualiza también el viewport |
| Sincronizar render | ❌ | Al cambiar de nivel, actualiza también el render |
| Activar atajos | ✅ | Registrar/quitar los atajos al vuelo |

---

## Conceptos clave (Multires)

- `sculpt_levels` — nivel activo en modo Sculpt.
- `levels` — nivel visible en viewport.
- `render_levels` — nivel usado en render.
- `total_levels` — niveles almacenados (techo para subir).

**Bajar de nivel nunca destruye el detalle esculpido de los niveles altos** — igual que en ZBrush. Solo *Borrar niveles superiores* elimina información, y por eso pide confirmación.

---

## Estructura del código

```
subdiv_levels/
├── blender_manifest.toml   # metadatos de la extensión (formato Blender 4.2+)
├── __init__.py             # register()/unregister()
├── operators.py            # 6 operadores sculpt_ext.*
├── ui.py                   # panel lateral
├── keymaps.py              # atajos (con limpieza completa)
├── preferences.py          # AddonPreferences
└── utils.py                # helpers: multires, cambio de nivel, estadísticas
```

### Operadores

| bl_idname | Función |
|---|---|
| `sculpt_ext.subdiv_smart` | Ctrl+D inteligente (crear / subir / añadir nivel) |
| `sculpt_ext.level_up` | Sube 1 nivel, nunca crea |
| `sculpt_ext.level_down` | Baja 1 nivel |
| `sculpt_ext.level_set` | Fija un nivel exacto (`level: int`) |
| `sculpt_ext.delete_higher` | Borra niveles superiores (con confirmación) |
| `sculpt_ext.apply_base` | Aplica desplazamiento a la base (con confirmación) |

---

## Pruebas

Smoke test sin GUI:

```
blender --background --factory-startup --python tests\smoke_test.py
```

Comprueba: creación del modificador, 3 subdivisiones, bajada/subida de niveles sin pérdida, borrado de superiores, fijado de nivel, aplicar base y doble ciclo de activación/desactivación. Termina con `SMOKE TEST: OK` (código de salida 0) si todo pasa.

---

## Hoja de ruta

- [ ] **Atajos para macropad con encoders**: dos hotkeys extra configurables en preferencias (p. ej. F13/F14) para subir/bajar nivel girando un encoder.
- [ ] **Fase 2 — Reconstruir niveles inferiores** (*unsubdivide*, `multires_rebuild_subdiv`): hueco reservado en la UI.
- [ ] Fuera de alcance por ahora: bake de displacement, multi-objeto, Geometry Nodes.

---

## Historial

| Fecha | Versión | Cambios |
|---|---|---|
| 2026-07-04 | 0.1.0 | MVP completo: operadores, panel, atajos, preferencias, smoke test, zip instalable |
