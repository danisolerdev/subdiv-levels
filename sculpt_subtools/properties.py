"""Propiedades registradas sobre tipos nativos de Blender.

Se registran sobre Object / Collection / Scene y se borran por completo en
unregister() para que el addon pueda activarse/desactivarse sin fugas.
"""

import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty


def register():
    bpy.types.Object.subtool_order = IntProperty(
        name="Orden",
        description="Posición del subtool dentro de su grupo",
        default=0,
    )
    bpy.types.Object.subtool_prev_hidden = BoolProperty(
        name="Oculto previo",
        description="Snapshot de visibilidad para restaurar tras salir de Solo",
        default=False,
    )
    bpy.types.Object.subtool_bool_op = EnumProperty(
        name="Rol booleano",
        description="Cómo participa este subtool en la booleana en vivo",
        items=(
            ('NONE', "Ninguno", "No participa en la booleana"),
            ('ADD', "Añadir", "Se une al resultado (unión)"),
            ('SUBTRACT', "Restar", "Se resta del resultado (diferencia)"),
            ('INTERSECT', "Intersecar", "Deja solo el volumen común (intersección)"),
        ),
        default='NONE',
    )
    bpy.types.Object.subtool_is_bool_result = BoolProperty(
        name="Resultado booleano",
        description="Marca el objeto de resultado del preview en vivo",
        default=False,
    )
    bpy.types.Collection.subtool_expanded = BoolProperty(
        name="Expandido",
        description="Si el grupo está desplegado en la paleta",
        default=True,
    )
    bpy.types.Scene.subtool_solo_active = StringProperty(
        name="Solo activo",
        description="Nombre del subtool aislado (vacío = sin Solo)",
        default="",
    )
    bpy.types.Scene.subtool_bool_edit = BoolProperty(
        name="Modo booleana",
        description="Mostrar los selectores de rol booleano en cada subtool",
        default=False,
    )
    bpy.types.Scene.subtool_bool_active = StringProperty(
        name="Preview booleano",
        description="Nombre del objeto de resultado del preview (vacío = sin preview)",
        default="",
    )


def unregister():
    del bpy.types.Scene.subtool_bool_active
    del bpy.types.Scene.subtool_bool_edit
    del bpy.types.Scene.subtool_solo_active
    del bpy.types.Collection.subtool_expanded
    del bpy.types.Object.subtool_is_bool_result
    del bpy.types.Object.subtool_bool_op
    del bpy.types.Object.subtool_prev_hidden
    del bpy.types.Object.subtool_order
