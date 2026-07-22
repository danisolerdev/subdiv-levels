"""Smoke test sin GUI del addon Sculpt Subtools.

Uso:
    blender --background --factory-startup --python tests/smoke_test.py

Registra el paquete directamente desde el repositorio (sin instalarlo como
extensión), ejerce los operadores y sale con código != 0 si algo falla.

Nota: el multi-object sculpt no se prueba aquí (no se reproduce en background).
"""

import os
import sys
import traceback

import bpy

# Hacer importable el paquete sculpt_subtools desde la raíz del repositorio.
# El paquete vive en <repo>/sculpt_subtools/, y este script en su carpeta tests/,
# así que la raíz está tres niveles por encima de __file__.
_REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import sculpt_subtools  # noqa: E402
from sculpt_subtools import utils  # noqa: E402


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_cube(name, location):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    return obj


def main() -> None:
    # Activar el addon (y comprobar que soporta ciclos de registro repetidos).
    sculpt_subtools.register()
    sculpt_subtools.unregister()
    sculpt_subtools.register()

    context = bpy.context
    scene = context.scene

    # Tool = colección con 3 subtools.
    tool = bpy.data.collections.new("Tool")
    scene.collection.children.link(tool)
    a = make_cube("ST_a", (0, 0, 0))
    b = make_cube("ST_b", (3, 0, 0))
    c = make_cube("ST_c", (6, 0, 0))
    for o in (a, b, c):
        for col in list(o.users_collection):
            col.objects.unlink(o)
        tool.objects.link(o)

    check(len(utils.all_subtools(tool)) == 3, "Deberían verse 3 subtools")
    check(utils.get_tool_root(a) == tool, "get_tool_root no devuelve el Tool")

    # Activar 'b' en modo Objeto.
    context.view_layer.objects.active = a
    result = bpy.ops.sculpt_ext.subtool_activate(name="ST_b")
    check('FINISHED' in result, f"activate(objeto) devolvió {result}")
    check(context.view_layer.objects.active == b, "El activo debería ser ST_b")

    # Entrar en Sculpt y saltar a 'c' (rebote) -> debe quedar en SCULPT.
    bpy.ops.object.mode_set(mode='SCULPT')
    result = bpy.ops.sculpt_ext.subtool_activate(name="ST_c")
    check('FINISHED' in result, f"activate(sculpt) devolvió {result}")
    check(context.view_layer.objects.active == c, "El activo debería ser ST_c")
    check(c.mode == 'SCULPT', f"Tras el salto, ST_c debería estar en SCULPT ({c.mode})")

    # Ciclar al siguiente subtool.
    result = bpy.ops.sculpt_ext.subtool_cycle(direction='NEXT')
    check('FINISHED' in result, f"cycle devolvió {result}")
    check(context.view_layer.objects.active != c, "cycle no cambió de subtool")

    bpy.ops.object.mode_set(mode='OBJECT')

    # Solo sobre 'a': el resto oculto; toggle: visibilidad restaurada.
    result = bpy.ops.sculpt_ext.subtool_solo(name="ST_a")
    check('FINISHED' in result, f"solo devolvió {result}")
    check(not a.hide_get(), "El aislado no debería estar oculto")
    check(b.hide_get() and c.hide_get(), "El resto debería ocultarse en Solo")
    check(scene.subtool_solo_active == "ST_a", "No se registró el Solo activo")
    result = bpy.ops.sculpt_ext.subtool_solo(name="ST_a")
    check('FINISHED' in result, f"solo(off) devolvió {result}")
    check(not b.hide_get() and not c.hide_get(), "Solo no restauró la visibilidad")
    check(scene.subtool_solo_active == "", "El Solo debería quedar limpio")

    # Duplicar / borrar.
    context.view_layer.objects.active = a
    a.select_set(True)
    result = bpy.ops.sculpt_ext.subtool_duplicate()
    check('FINISHED' in result, f"duplicate devolvió {result}")
    check(len(utils.all_subtools(tool)) == 4, "Duplicar debería dejar 4 subtools")

    result = bpy.ops.sculpt_ext.subtool_delete('EXEC_DEFAULT')
    check('FINISHED' in result, f"delete devolvió {result}")
    check(len(utils.all_subtools(tool)) == 3, "Borrar debería dejar 3 subtools")

    # Grupo + mover.
    result = bpy.ops.sculpt_ext.subtool_group_new(name="Group_1")
    check('FINISHED' in result, f"group_new devolvió {result}")
    group = bpy.data.collections.get("Group_1")
    check(group is not None and group in list(tool.children), "El grupo no se creó bajo el Tool")

    active = context.view_layer.objects.active
    result = bpy.ops.sculpt_ext.subtool_move_to_group(group="Group_1")
    check('FINISHED' in result, f"move_to_group devolvió {result}")
    check(active.name in group.objects, "El subtool no se movió al grupo")

    # Reordenar dentro del Tool.
    remaining = utils.subtools_of(tool, 'MANUAL')
    if len(remaining) >= 2:
        context.view_layer.objects.active = remaining[1]
        remaining[1].select_set(True)
        before = remaining[1].name
        result = bpy.ops.sculpt_ext.subtool_move(direction='UP')
        check('FINISHED' in result, f"move devolvió {result}")
        after = utils.subtools_of(tool, 'MANUAL')
        check(after[0].name == before, "move UP no reordenó el subtool")

    # --- Fase 2: crear, espejar, splits, multires, globales ---

    def link_cube(name):
        bpy.ops.mesh.primitive_cube_add()
        o = bpy.context.active_object
        o.name = name
        for col in list(o.users_collection):
            col.objects.unlink(o)
        tool.objects.link(o)
        return o

    # Añadir subtool (primitiva) al Tool.
    base = utils.subtools_of(tool, 'MANUAL')[0]
    context.view_layer.objects.active = base
    n = len(utils.all_subtools(tool))
    result = bpy.ops.sculpt_ext.subtool_add(kind='CUBE')
    check('FINISHED' in result, f"add devolvió {result}")
    check(len(utils.all_subtools(tool)) == n + 1, "add no incrementó el nº de subtools")

    # Espejar el subtool activo (el cubo recién añadido).
    n = len(utils.all_subtools(tool))
    result = bpy.ops.sculpt_ext.subtool_mirror(axis='X')
    check('FINISHED' in result, f"mirror devolvió {result}")
    check(len(utils.all_subtools(tool)) == n + 1, "mirror no creó la copia")

    # Multires del activo: subdividir y navegar niveles.
    active = context.view_layer.objects.active
    mod = active.modifiers.new(name="Multires", type='MULTIRES')
    context.view_layer.objects.active = active
    bpy.ops.object.multires_subdivide(modifier="Multires", mode='CATMULL_CLARK')
    bpy.ops.object.multires_subdivide(modifier="Multires", mode='CATMULL_CLARK')
    check(mod.total_levels == 2, f"total_levels = {mod.total_levels}, esperado 2")
    result = bpy.ops.sculpt_ext.subtool_multires_step(delta=-1)
    check('FINISHED' in result, f"multires_step(-1) devolvió {result}")
    check(mod.sculpt_levels == 1, f"sculpt_levels = {mod.sculpt_levels}, esperado 1")
    bpy.ops.sculpt_ext.subtool_multires_step(delta=1)
    check(mod.sculpt_levels == 2, f"sculpt_levels = {mod.sculpt_levels}, esperado 2")

    # Split por Face Set: cubo con 2 grupos -> 2 subtools (neto +1).
    fsobj = link_cube("FS_cube")
    me = fsobj.data
    attr = me.attributes.new(name=".sculpt_face_set", type='INT', domain='FACE')
    for i in range(len(me.polygons)):
        attr.data[i].value = 1 if i < len(me.polygons) // 2 else 2
    n = len(utils.all_subtools(tool))
    context.view_layer.objects.active = fsobj
    result = bpy.ops.sculpt_ext.subtool_split_faceset()
    check('FINISHED' in result, f"split_faceset devolvió {result}")
    check(len(utils.all_subtools(tool)) == n + 1, "split por Face Set no dio 2 piezas")

    # Split por máscara: enmascarar la cara +X.
    mobj = link_cube("M_cube")
    me = mobj.data
    mask = me.attributes.new(name=".sculpt_mask", type='FLOAT', domain='POINT')
    for i in range(len(me.vertices)):
        mask.data[i].value = 1.0 if me.vertices[i].co.x > 0 else 0.0
    n = len(utils.all_subtools(tool))
    context.view_layer.objects.active = mobj
    result = bpy.ops.sculpt_ext.subtool_split_mask()
    check('FINISHED' in result, f"split_mask devolvió {result}")
    check(len(utils.all_subtools(tool)) == n + 1, "split por máscara no creó la pieza")

    # Renombrar un subtool (ruta execute directa, sin diálogo).
    victim = utils.subtools_of(tool, 'MANUAL')[0]
    old = victim.name
    result = bpy.ops.sculpt_ext.subtool_rename(
        'EXEC_DEFAULT', target=old, new_name="Renombrado")
    check('FINISHED' in result, f"rename devolvió {result}")
    check(victim.name == "Renombrado", f"rename no aplicó el nombre ({victim.name})")

    # Mostrar todos.
    for o in utils.all_subtools(tool):
        o.hide_set(True)
    context.view_layer.objects.active = utils.subtools_of(tool, 'MANUAL')[0]
    result = bpy.ops.sculpt_ext.subtool_show_all()
    check('FINISHED' in result, f"show_all devolvió {result}")
    check(all(not o.hide_get() for o in utils.all_subtools(tool)),
          "show_all no mostró todos los subtools")

    # --- Booleanas ---
    bcoll = bpy.data.collections.new("BoolTool")
    scene.collection.children.link(bcoll)

    def bool_cube(name, loc):
        bpy.ops.mesh.primitive_cube_add(location=loc)
        o = bpy.context.active_object
        o.name = name
        for c in list(o.users_collection):
            c.objects.unlink(o)
        bcoll.objects.link(o)
        return o

    # Live boolean: A (añadir) menos B (restar).
    A = bool_cube("B_A", (0, 0, 0))
    B = bool_cube("B_B", (0.5, 0.5, 0.5))
    A.subtool_bool_op = 'ADD'
    B.subtool_bool_op = 'SUBTRACT'
    context.view_layer.objects.active = A
    result = bpy.ops.sculpt_ext.subtool_bool_preview()
    check('FINISHED' in result, f"bool_preview devolvió {result}")
    check(scene.subtool_bool_active != "", "el preview no se activó")
    res = bpy.data.objects.get(scene.subtool_bool_active)
    check(res is not None and len(res.modifiers) == 2, "el resultado no tiene 2 modificadores")
    check(A.hide_get() and B.hide_get(), "los operandos deberían ocultarse en preview")

    context.view_layer.objects.active = res
    result = bpy.ops.sculpt_ext.subtool_bool_apply()
    check('FINISHED' in result, f"bool_apply devolvió {result}")
    check(scene.subtool_bool_active == "", "apply no limpió el preview")
    check(bpy.data.objects.get("B_A") is None and bpy.data.objects.get("B_B") is None,
          "apply no borró los operandos")
    check(len(res.data.polygons) > 0 and len(res.modifiers) == 0,
          "el resultado quedó vacío o con modificadores sin aplicar")

    # Booleana directa: C menos D (por selección).
    C = bool_cube("D_A", (0, 0, 0))
    D = bool_cube("D_B", (0.5, 0.5, 0.5))
    for o in context.selected_objects:
        o.select_set(False)
    C.select_set(True)
    D.select_set(True)
    context.view_layer.objects.active = C
    result = bpy.ops.sculpt_ext.subtool_bool_direct(op='DIFFERENCE')
    check('FINISHED' in result, f"bool_direct devolvió {result}")
    check(bpy.data.objects.get("D_B") is None, "bool_direct no borró el operando")
    check(len(C.data.polygons) > 0, "bool_direct dejó una malla vacía")

    # Desactivar sin errores.
    sculpt_subtools.unregister()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.stdout.write("SMOKE TEST: FAILED\n")
        sys.exit(1)
    sys.stdout.write("SMOKE TEST: OK\n")
    sys.exit(0)
