"""Smoke test sin GUI del addon Subdiv Levels.

Uso:
    blender --background --factory-startup --python tests/smoke_test.py

Registra el paquete directamente desde el repositorio (sin instalarlo como
extensión), ejerce los operadores y sale con código != 0 si algo falla.
"""

import os
import sys
import traceback

import bpy

# Hacer importable el paquete subdiv_levels desde la raíz del repositorio.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import subdiv_levels  # noqa: E402


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def get_multires(obj):
    for mod in obj.modifiers:
        if mod.type == 'MULTIRES':
            return mod
    return None


def main() -> None:
    # Activar el addon (y comprobar que soporta ciclos de registro repetidos).
    subdiv_levels.register()
    subdiv_levels.unregister()
    subdiv_levels.register()

    # Cubo nuevo como objeto activo (se lanza con --factory-startup).
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.view_layer.objects.active
    check(obj is not None and obj.type == 'MESH', "No hay cubo activo")

    # Ctrl+D x3: crea el multires y añade 3 niveles.
    for i in range(3):
        result = bpy.ops.sculpt_ext.subdiv_smart()
        check('FINISHED' in result, f"subdiv_smart #{i + 1} devolvió {result}")

    mod = get_multires(obj)
    check(mod is not None, "No se creó el modificador Multires")
    check(mod.name == "Multires", f"Nombre inesperado: {mod.name}")
    check(mod.total_levels == 3, f"total_levels = {mod.total_levels}, esperado 3")
    check(mod.sculpt_levels == 3, f"sculpt_levels = {mod.sculpt_levels}, esperado 3")
    check(mod.levels == 3, f"levels = {mod.levels}, esperado 3 (sync_viewport)")

    # Bajar 2 niveles.
    for i in range(2):
        result = bpy.ops.sculpt_ext.level_down()
        check('FINISHED' in result, f"level_down #{i + 1} devolvió {result}")
    check(mod.sculpt_levels == 1, f"sculpt_levels = {mod.sculpt_levels}, esperado 1")
    check(mod.total_levels == 3, "Bajar de nivel no debe destruir niveles")

    # Subir 1 nivel sin crear ninguno nuevo.
    result = bpy.ops.sculpt_ext.level_up()
    check('FINISHED' in result, f"level_up devolvió {result}")
    check(mod.sculpt_levels == 2, f"sculpt_levels = {mod.sculpt_levels}, esperado 2")
    check(mod.total_levels == 3, "level_up nunca debe crear niveles")
    bpy.ops.sculpt_ext.level_down()

    # Borrar niveles superiores (EXEC_DEFAULT salta el diálogo de confirmación).
    result = bpy.ops.sculpt_ext.delete_higher('EXEC_DEFAULT')
    check('FINISHED' in result, f"delete_higher devolvió {result}")
    check(mod.total_levels == 1, f"total_levels = {mod.total_levels}, esperado 1")

    # Fijar nivel exacto y aplicar base.
    result = bpy.ops.sculpt_ext.level_set(level=0)
    check('FINISHED' in result, f"level_set devolvió {result}")
    check(mod.sculpt_levels == 0, f"sculpt_levels = {mod.sculpt_levels}, esperado 0")

    result = bpy.ops.sculpt_ext.apply_base('EXEC_DEFAULT')
    check('FINISHED' in result, f"apply_base devolvió {result}")

    # Desactivar sin errores.
    subdiv_levels.unregister()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.stdout.write("SMOKE TEST: FAILED\n")
        sys.exit(1)
    sys.stdout.write("SMOKE TEST: OK\n")
    sys.exit(0)
