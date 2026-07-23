# Blender Sculpt Addons

### ⬇️ [Descargar los addons (última Release)](https://github.com/danisolerdev/blender-sculpt-addons/releases/latest)

Colección de **extensiones para Blender 5.x** que llevan al modo Sculpt flujos de trabajo de
**ZBrush / Nomad Sculpt** que Blender no ofrece de serie: niveles de subdivisión, paleta de
subtools y anillo doble de pincel.

Cada addon es independiente, autocontenido e instalable por separado. No reimplementan
funcionalidad que Blender ya tiene: se apoyan en sus sistemas nativos (Multires, colecciones,
pinceles) y aportan la **UX rápida** que falta para esculpir con comodidad.

> Blender **5.0+** (desarrollados y probados en 5.1.2) · Licencia **GPL-3.0-or-later** ·
> Interfaz traducida a 8 idiomas.

---

## Addons

| Addon | Qué aporta | Versión | Documentación |
|---|---|---|---|
| **[Subdiv Levels](subdiv_levels/)** | Niveles de subdivisión estilo ZBrush/Nomad sobre el modificador Multires: subir/bajar/añadir nivel con atajos y panel | 0.3.0 | [Doc](subdiv_levels/docs/Subdiv%20Levels%20-%20Documentacion.md) |
| **[Sculpt Subtools](sculpt_subtools/)** | Paleta de subtools estilo ZBrush: saltar, aislar, agrupar, unir/partir, booleanas y miniaturas | 0.4.0 | [Doc](sculpt_subtools/docs/Sculpt%20Subtools%20-%20Documentacion.md) · [Especificación](sculpt_subtools/docs/Sculpt%20Subtools%20-%20Especificacion.md) |
| **[Brush Focus Ring](brush_focus_ring/)** | Doble circunferencia de pincel (foco + influencia) y atajos de encoder de macropad | 0.7.4 | [Doc](brush_focus_ring/docs/Brush%20Focus%20Ring%20-%20Documentacion.md) |

---

## Instalación

Cada addon se instala como una extensión independiente:

1. Ve a la pestaña **[Releases](../../releases)** del repositorio y descarga el zip del addon
   que quieras (p. ej. `brush_focus_ring-0.7.4.zip`).
2. En Blender: **Edit → Preferences → Get Extensions → ⌄ → Install from Disk…**
3. Selecciona el zip. Se instala y activa automáticamente.

Puedes instalar solo los que te interesen; no dependen entre sí.

> El botón verde **Code → Download ZIP** descarga el repositorio entero (código fuente), que
> **no** es instalable en Blender directamente. Los zips listos para instalar están en *Releases*.

---

## Generar los zips

Los paquetes se construyen con el script incluido, que lee la versión de cada
`blender_manifest.toml` y excluye `__pycache__` / `.pyc`:

```
python build_addons.py                 # los addons por defecto
python build_addons.py subdiv_levels   # solo uno
```

Los zips se escriben en `dist/` (ignorada por git). Alternativa nativa de Blender:

```
blender --command extension build --source-dir subdiv_levels --output-dir dist
```

---

## Estructura del repositorio

```
.
├── subdiv_levels/      # addon: niveles de subdivisión (Multires)
│   └── docs/
├── sculpt_subtools/    # addon: paleta de subtools
│   └── docs/
├── brush_focus_ring/   # addon: anillo doble de pincel
│   └── docs/
├── build_addons.py     # empaquetador de extensiones a dist/
├── PUBLICACION.md      # notas de publicación
├── LICENSE             # GPL-3.0-or-later
└── README.md           # este índice
```

Cada carpeta de addon sigue el formato de **extensión de Blender 4.2+** (`blender_manifest.toml`
en la raíz, sin `bl_info`), con `register()` / `unregister()` limpios y traducciones propias.

---

## Desarrollo

- **Compatibilidad 5.x**: acceso a propiedades por atributo (no tipo diccionario), sin importar
  módulos internos, registro con listas de clases y limpieza total en `unregister()`.
- **Tests**: cada addon con lógica verificable trae un smoke test sin GUI:
  ```
  blender --background --factory-startup --python <addon>/tests/smoke_test.py
  ```
- **Idiomas**: cada addon incluye `translations.py` con español, francés, alemán, chino
  simplificado, japonés, coreano, portugués e italiano.

---

## Licencia

Todo el proyecto se distribuye bajo **GPL-3.0-or-later**, como requiere el ecosistema de addons
de Blender. Texto completo en [LICENSE](LICENSE).

Mantenedor: Dani · danielsolerdev@gmail.com
