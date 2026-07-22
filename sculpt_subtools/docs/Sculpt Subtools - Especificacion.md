# Especificación técnica — Addon "Sculpt Subtools" para Blender

Documento de especificación única del addon. Sigue este documento como blueprint.
Si algo no está definido aquí, preguntar antes de asumir. Mismo estilo y reglas que
el `CLAUDE.md` de Subdiv Levels.

## 1. Contexto y objetivo

Replicar la experiencia de los **SubTools de ZBrush** dentro de Blender 5.x: una
**paleta** siempre a mano en modo Sculpt para gestionar las mallas de una escena
como subtools — saltar entre ellas, aislar (solo), ocultar, duplicar, borrar,
renombrar, unir/partir, agrupar y reordenar — **sin salir del modo Sculpt** más de
lo imprescindible.

Punto conceptual clave (define todo el addon): **en Blender los subtools ya existen.**
ZBrush inventó los SubTools porque no tiene sistema de escena; Blender sí (objetos,
colecciones, Outliner). Por tanto este addon **NO reimplementa un modelo de datos
propio**: cada objeto malla *es* un subtool y cada colección *es* un "Tool". El
addon aporta únicamente la **UX/paleta** que Blender no ofrece de serie para esculpir.

## 2. Hallazgos del spike (fundamento de diseño)

Validado en `blender --background` sobre Blender 5.1.0 (ver `tests/` / spike previo):

- **Multi-object sculpt (esculpir varias mallas a la vez): inconcluso en headless** y,
  sobre todo, **innecesario**: ZBrush tampoco esculpe varios subtools a la vez. El
  modelo correcto es **un subtool activo** y "clic para cambiar".
- **Saltar de subtool = rebote de modo `OBJECT → cambiar activo → SCULPT`: PROBADO y
  fiable**, incluso con Multires en los objetos. Es rápido (ms) y sin el riesgo que
  hundió a Face Set Guided Remesh. **Este es el mecanismo base.**
- **Agrupar/mover con sub-colecciones: PROBADO.** El modelo `Tool > Grupo > SubTool`
  con colecciones anidadas es sólido, y la visibilidad de grupo la da Blender gratis.
- **Solo (ocultar el resto):** el objeto activo aguanta en Sculpt; los ocultos salen
  de Sculpt (al re-mostrarlos habrá que re-entrar, cubierto por el rebote).

Fleco a verificar en GUI (no bloquea): si el multi-object sculpt de la interfaz
permitiera "clic = cambiar activo instantáneo sin rebote", se añadiría como vía
premium opcional. Mientras, se construye sobre el rebote.

## 3. Alcance del MVP

Incluido:

- **Paleta** en la barra lateral (N) del Viewport 3D, pestaña "Subtools", visible en
  modo Sculpt y modo Objeto.
- **Árbol Tool > Grupos > SubTools** dibujado a mano (Blender no tiene UIList en árbol).
- **Activar** un subtool (saltar de activo) por clic, con rebote de modo si estamos en
  Sculpt. Cíclico prev/siguiente por operador.
- **Visibilidad** por ítem (ojito) y **Solo/aislar** el activo (con restaurar estado).
- **Duplicar**, **borrar** (con confirmación) y **renombrar** (inline).
- **Merge** (unir seleccionados en el activo) y **Split por partes sueltas**.
- **Agrupar**: crear sub-colección y **mover** subtool a un grupo.
- **Reordenar** (subir/bajar) mediante propiedad de orden.
- Estadística mínima en el pie: nº de subtools y nombre + recuento de caras del activo.

Fuera de alcance (NO implementar sin pedirlo):

- Split por máscara y split por Face Set (fase 2).
- Multi-object sculpt simultáneo (vía premium, solo si la GUI lo confirma).
- Merge que preserve niveles de Multires de cada subtool (Blender pierde/aplica el
  Multires al hacer `join`; en MVP se avisa, no se resuelve).
- Reordenar por drag & drop.
  (Miniaturas/preview por subtool: implementadas en fase 5, ver §15.)

## 4. Estructura del proyecto

Formato **extensión** de Blender 4.2+ (vigente en 5.x), no addon clásico:

```
sculpt_subtools/
├── blender_manifest.toml
├── __init__.py          # register()/unregister(), importa los módulos
├── operators.py         # bpy.types.Operator (sculpt_ext.subtool_*)
├── ui.py                # panel/paleta (dibujo del árbol a mano)
├── keymaps.py           # atajos opcionales
├── preferences.py       # AddonPreferences
├── properties.py        # propiedades registradas en tipos nativos (orden, solo, expand)
├── utils.py             # helpers: Tool root, recorrido de árbol, validaciones
├── docs/
└── tests/smoke_test.py
```

`blender_manifest.toml` mínimo:

```toml
schema_version = "1.0.0"
id = "sculpt_subtools"
version = "0.1.0"
name = "Sculpt Subtools"
tagline = "Paleta de subtools estilo ZBrush para Sculpt"
maintainer = "Dani <danielsolerdev@gmail.com>"
type = "add-on"
tags = ["Sculpt", "Mesh"]
blender_version_min = "5.0.0"
license = ["SPDX:GPL-3.0-or-later"]
```

No usar `bl_info`. El `id` del manifest define el paquete.

## 5. Modelo de datos y helpers (utils.py)

Mapeo (sin estado duplicado propio; la verdad vive en las colecciones/objetos):

```
Colección "Tool"        = agrupación raíz que muestra la paleta
├─ Sub-colección "Grupo" = folder de subtools
│   ├─ Objeto malla       = SubTool
│   └─ Objeto malla       = SubTool
└─ Objeto malla           = SubTool suelto
```

Reglas y helpers:

- `get_tool_root(obj) -> Collection`: el "Tool" es la colección **ancestro del objeto
  activo cuyo padre es la Scene Collection** (la más externa bajo la escena). Se sube
  desde la colección directa del objeto hasta ese ancestro. Si el objeto solo está en
  la Scene Collection, el Tool es la propia Scene Collection.
- `iter_subtree(coll)`: recorrido en orden para dibujar (grupo → sus objetos → sus
  hijos), respetando `subtool_order` para ordenar objetos dentro de cada colección.
- `subtools_of(coll)`: objetos malla directos de una colección.
- `is_subtool(obj)`: `obj is not None and obj.type == 'MESH'`.
- No usar acceso tipo diccionario a props de `bpy.props` (regla 5.x). Acceso por atributo.

## 6. Propiedades registradas (properties.py)

Anotación con `:` siempre; registro sobre tipos nativos y **limpieza en unregister**.

- `bpy.types.Object.subtool_order: IntProperty(default=0)` — orden dentro de su
  colección (para subir/bajar).
- `bpy.types.Object.subtool_prev_hidden: BoolProperty(default=False)` — snapshot de
  visibilidad para restaurar tras Solo.
- `bpy.types.Collection.subtool_expanded: BoolProperty(default=True)` — plegado del
  grupo en la paleta.
- `bpy.types.Scene.subtool_solo_active: StringProperty(default="")` — nombre del
  subtool en Solo (vacío = sin Solo).

En `unregister()`, borrar cada una con `del bpy.types.X.prop`.

## 7. Operadores (operators.py)

Prefijo `bl_idname`: `sculpt_ext.subtool_*` (misma familia que Subdiv Levels; los
`bl_idname` son únicos por sufijo, no colisionan). Todos con
`bl_options = {'REGISTER', 'UNDO'}` salvo donde se indique. `poll()` estricto: nunca
lanzar excepción con contexto inválido.

| bl_idname | Comportamiento |
|---|---|
| `sculpt_ext.subtool_activate` | Prop `name: StringProperty`. Hace activo ese objeto. Si el modo actual es Sculpt: rebote `OBJECT → deseleccionar → seleccionar+activar → SCULPT` (respetando la preferencia `switch_reenters_sculpt`). Si el objeto está oculto, lo muestra antes. Si estamos en Objeto: solo selecciona+activa. |
| `sculpt_ext.subtool_cycle` | Prop `direction: EnumProperty(PREV/NEXT)`. Calcula el siguiente subtool del Tool en orden de árbol y delega en `subtool_activate`. |
| `sculpt_ext.subtool_toggle_visible` | Prop `name`. `obj.hide_set(not obj.hide_get())`. |
| `sculpt_ext.subtool_solo` | Prop `name`. Toggle. Al activar: guarda `subtool_prev_hidden` de cada subtool del Tool, oculta todos menos el objetivo (o su grupo si `solo_includes_group`), fija `scene.subtool_solo_active`. Al desactivar: restaura visibilidad desde el snapshot y limpia el flag. |
| `sculpt_ext.subtool_duplicate` | Duplica el activo (rebote a OBJECT si hace falta), lo deja en la misma colección y lo activa. Copia Multires con el objeto. |
| `sculpt_ext.subtool_delete` | `invoke_confirm` (según `confirm_delete`), elimina el objeto y su malla si queda sin usuarios. |
| `sculpt_ext.subtool_move` | Prop `direction: EnumProperty(UP/DOWN)`. Intercambia `subtool_order` con el vecino dentro de la colección. |
| `sculpt_ext.subtool_move_to_group` | Prop `group: StringProperty`. Desvincula el activo de su colección y lo vincula a la colección grupo indicada. |
| `sculpt_ext.subtool_group_new` | Prop `name`. Crea una sub-colección dentro del Tool root. |
| `sculpt_ext.subtool_merge` | `invoke_confirm` (según `confirm_merge`). Une los subtools seleccionados en el activo con `object.join` (rebote a OBJECT). Avisa con `self.report({'WARNING'})` de que el Multires no se conserva. |
| `sculpt_ext.subtool_split_loose` | Separa el activo por partes sueltas (`mesh.separate(type='LOOSE')` con rebote a EDIT y vuelta). Los nuevos objetos entran como subtools de la misma colección. |
| `sculpt_ext.subtool_toggle_expand` | Prop `collection: StringProperty`. Alterna `subtool_expanded` del grupo. |

Notas de contexto (mismas que Subdiv Levels):

- `poll()` base: hay objeto activo, es `'MESH'`, y no está en modo Edit.
- Tras cambios de visibilidad/activo desde botón: `context.area.tag_redraw()` y, si hace
  falta refresco de datos, `obj.update_tag()`.
- Los rebotes de modo usan `bpy.ops.object.mode_set(mode=...)`; guardar y restaurar el
  modo previo, y **dejar siempre el objeto correcto activo/seleccionado** al terminar
  (patrón `_restore_active`).

## 8. Panel / paleta (ui.py)

`bpy.types.Panel`, `bl_space_type='VIEW_3D'`, `bl_region_type='UI'`,
`bl_category='Subtools'`. Visible en Sculpt y Objeto. Contenido:

1. Cabecera: nombre del Tool root + botón "Nuevo grupo" (`subtool_group_new`).
2. **Árbol dibujado a mano** (no hay UIList en árbol). Recorrer `iter_subtree` del Tool:
   - **Fila de grupo**: triángulo de plegado (`subtool_toggle_expand`, icono
     `DISCLOSURE_TRI_DOWN/RIGHT`), ojito de colección (visibilidad nativa), nombre.
   - **Fila de subtool** (indentada): si `show_thumbnails`, miniatura a la izquierda
     (`layout.template_icon`, escala `thumbnail_scale`) y los controles apilados a su
     derecha. Controles: ojito (`subtool_toggle_visible`), icono de
     resaltado del activo (`RADIOBUT_ON` si `obj == context.object`, si no `RADIOBUT_OFF`),
     campo de nombre editable inline (`row.prop(obj, "name", text="")`), botón Solo
     (`subtool_solo`, icono `PINNED`/`RESTRICT_VIEW`). Clic en el nombre/icono de
     activo → `subtool_activate(name=obj.name)`.
   - Si el grupo está plegado (`subtool_expanded == False`), no dibujar sus hijos.
3. Fila de acciones: `+`/`−` (duplicar/borrar), subir/bajar (`subtool_move`),
   `merge`, `split_loose`, `move_to_group`.
4. Pie: `N subtools · Activo: <nombre> (<caras> caras)`. El recuento de caras solo del
   activo (`len(obj.data.polygons)`), no iterar mallas evaluadas en cada draw.

El panel **no guarda estado propio**: siempre refleja colecciones/objetos reales.

## 9. Atajos (keymaps.py)

Registrar en el keymap `"Sculpt"` (y opcionalmente `"Object Mode"`). Guardar las
entradas en `addon_keymaps` y limpiarlas en `unregister()`. Desactivables desde
preferencias (`enable_hotkeys`, **por defecto False** para no colisionar):

- Sugeridos (off por defecto): `Alt+Up` → `subtool_cycle(direction='PREV')`,
  `Alt+Down` → `subtool_cycle(direction='NEXT')`.

No registrar por defecto atajos que pisen el keymap de Sculpt (muy poblado).

## 10. Preferencias (preferences.py)

`AddonPreferences` con `bl_idname = __package__`:

- `switch_reenters_sculpt`: Bool, default True — al saltar de subtool desde Sculpt,
  rebotar y volver a Sculpt (si False, queda en Objeto).
- `solo_includes_group`: Bool, default False — Solo mantiene visible todo el grupo del
  objetivo, no solo el objeto.
- `confirm_delete`: Bool, default True.
- `confirm_merge`: Bool, default True.
- `enable_hotkeys`: Bool, default False.
- `sort_mode`: Enum `MANUAL` (por `subtool_order`, default) / `NAME`.
- `show_thumbnails`: Bool, default True — dibujar la miniatura de cada subtool.
- `auto_thumbnails`: Bool, default True — recapturar al salir de un subtool y al
  crear/duplicar/separar.
- `thumbnail_scale`: Float, default 3.0 (min 1, max 8) — tamaño de la miniatura.

Igual que en Subdiv Levels, prever un `_FallbackPrefs` para cuando el paquete se
registra a mano (smoke test).

## 11. Compatibilidad Blender 5.x — reglas obligatorias

- No usar acceso tipo diccionario a propiedades `bpy.props` (`obj['prop']`): eliminado
  en 5.0. Acceso por atributo.
- No importar módulos internos (`bl_console_utils`, etc.).
- Registro con `classes = (...)` + bucle `register_class` en `register()` y orden
  inverso en `unregister()`.
- Propiedades sobre tipos nativos (`bpy.types.Object`, `Collection`, `Scene`)
  **registradas y borradas** limpiamente (activar/desactivar N veces sin fugas ni
  errores; keymaps y props eliminados por completo).
- Anotaciones con `:` (annotation syntax), nunca `=`.

## 12. Convenciones de código

- Python con type hints donde aporte; docstrings breves en español.
- Nada de `print()` en el código final: `self.report()` en operadores.
- Ningún operador lanza excepción con contexto inválido: `poll()` estricto.
- Mensajes de UI en español.

## 13. Pruebas y verificación

Smoke test sin GUI (`tests/smoke_test.py`),
`blender --background --factory-startup --python tests/smoke_test.py`:

1. Activa el addon; crea una colección Tool con 3 cubos como subtools.
2. `subtool_activate` sobre otro subtool en modo Objeto → comprueba objeto activo.
3. Entra en Sculpt, `subtool_activate` a otro → comprueba activo y (rebote) que vuelve
   a `mode == 'SCULPT'`.
4. `subtool_solo` sobre uno → comprueba que los demás quedan ocultos; toggle → comprueba
   visibilidad restaurada.
5. `subtool_duplicate` → nº de subtools +1; `subtool_delete` → −1.
6. `subtool_group_new` + `subtool_move_to_group` → el objeto queda en el grupo.
7. `subtool_move` UP/DOWN → `subtool_order` intercambiado.
8. Activar/desactivar el addon dos veces sin errores en consola.

Salir con código ≠ 0 si algo falla. Nota: el multi-object sculpt no se prueba headless.

Verificación manual mínima: paleta visible en Sculpt, saltar entre subtools, Solo y su
restauración, y activar/desactivar el addon dos veces sin errores.

## 14. Criterios de aceptación

1. La paleta muestra el árbol Tool > Grupos > SubTools del objeto activo y siempre
   refleja el estado real (sin estado duplicado).
2. Clic en un subtool lo hace activo; estando en Sculpt, el rebote es instantáneo y
   deja el modo en Sculpt.
3. Solo aísla el activo y su desactivación restaura exactamente la visibilidad previa.
4. Duplicar/borrar/renombrar/mover/agrupar/reordenar operan sobre objetos y colecciones
   reales, visibles también en el Outliner.
5. Instalable como extensión (zip con `blender_manifest.toml`) en Blender 5.1.2.
6. El smoke test pasa en modo background y el addon activa/desactiva sin fugas.

## 15. Fases

- **Fase 1 (MVP) — hecha:** todo lo de §3 "Incluido".
- **Fase 2 — hecha** (implementada con bmesh sobre atributos, sin operadores nativos
  de máscara, que NO existen en 5.1: `mesh.paint_mask_slice`/`paint_mask_extract`
  ausentes — verificado en spike):
  - Crear/Append: `subtool_add` (primitiva) y `subtool_mirror` (copia reflejada).
  - Splits: `subtool_split_faceset` (por `.sculpt_face_set`) y `subtool_split_mask`
    (por `.sculpt_mask`, cara enmascarada si la media de sus vértices ≥ 0.5).
  - Globales: `subtool_show_all`, `subtool_frame_active`.
  - Integración Subdiv Levels: `subtool_multires_step` + fila de nivel en la paleta si
    el activo tiene Multires (autocontenido, sin dependencia dura del otro addon).
- **Fase 3 — booleanas (hecha):** flujo Live Boolean + directas, integrado en los
  subtools (bajo riesgo, sobre el modificador Boolean nativo, solver Exact):
  - Rol por subtool (`subtool_bool_op`: NONE/ADD/SUBTRACT/INTERSECT), editable en la
    paleta con el toggle "Roles".
  - `subtool_bool_preview`: objeto de resultado con un modificador Boolean por operando
    (orden: unir → intersecar → restar), operandos ocultos; toggle para quitarlo.
  - `subtool_bool_apply`: hornea el resultado y borra los operandos.
  - `subtool_bool_direct` (UNION/DIFFERENCE/INTERSECT): booleana rápida activo vs resto
    de seleccionados, aplicada al momento.
- **Fase 5 — miniaturas (hecha):** miniatura por subtool en la paleta, estilo ZBrush
  (`preview.py`). Captura del viewport con `GPUOffScreen.draw_view3d`, tomando la
  orientación actual del viewport y encuadrando la caja del objeto; se cachea en un
  `bpy.utils.previews` y se dibuja con `layout.template_icon`. Refresco: botón manual
  (`subtool_thumbnails_refresh`) + automático al salir de un subtool y al
  crear/duplicar/separar (`auto_thumbnails`). Sin GPU (background) degrada a un
  marcador de posición gris; no se puede probar en el smoke test headless, validado
  en GUI (128×128, imagen real). Nunca se regenera en `draw()` (el panel se redibuja
  sin parar): siempre cacheado.
- **Fase 4 (pendiente):** multi-object sculpt como vía premium si la GUI lo confirma;
  extract desde máscara con grosor.
