"""Miniaturas por subtool: captura del viewport a un ImagePreview cacheado.

Estilo ZBrush: cada subtool muestra una miniatura en su fila de la paleta. La
imagen se genera con `GPUOffScreen.draw_view3d`, tomando la orientación actual
del viewport (matcap/ángulo del usuario) y encuadrando la caja del objeto.

Restricción clave verificada en el spike: `draw_view3d` necesita GPU y **no
funciona en modo background** (`blender --background`). Por eso toda la captura
está aislada aquí y degrada con elegancia: sin GPU, `get_icon_id` devuelve un
marcador de posición gris y nada falla. La validación visual real es en GUI.
"""

import bpy

# Colección de previews del addon (creada en register()).
_previews = None
# Claves con miniatura real ya capturada (para no mostrar el marcador).
_captured = set()

_PLACEHOLDER = "__placeholder__"
_THUMB_SIZE = 128  # resolución interna de la miniatura (px, cuadrada).


# --- Caché --------------------------------------------------------------------

def _key(obj) -> str:
    """Clave de caché estable: sobrevive a renombrados dentro de la sesión."""
    try:
        return str(obj.session_uid)
    except AttributeError:
        return obj.name


def _set_pixels(preview, flat) -> None:
    """Vuelca un array plano RGBA (float) en el preview, con fallback sin numpy."""
    try:
        preview.image_pixels_float.foreach_set(flat)
    except (AttributeError, TypeError):
        preview.image_pixels_float[:] = (
            flat.tolist() if hasattr(flat, "tolist") else list(flat)
        )


def _build_placeholder() -> None:
    """Marcador de posición: recuadro gris para subtools sin miniatura."""
    try:
        import numpy as np
    except Exception:
        return
    size = 64
    img = np.full((size, size, 4), 0.18, dtype=np.float32)
    img[..., 3] = 1.0
    img[0, :, :3] = img[-1, :, :3] = 0.30
    img[:, 0, :3] = img[:, -1, :3] = 0.30
    preview = _previews.new(_PLACEHOLDER)
    preview.image_size = (size, size)
    _set_pixels(preview, img.reshape(-1))


def _placeholder_icon_id() -> int:
    if _previews is None:
        return 0
    preview = _previews.get(_PLACEHOLDER)
    return preview.icon_id if preview is not None else 0


def get_icon_id(obj) -> int:
    """icon_id de la miniatura del objeto, o el del marcador si aún no hay."""
    if _previews is not None and obj is not None:
        key = _key(obj)
        if key in _captured:
            preview = _previews.get(key)
            if preview is not None:
                return preview.icon_id
    return _placeholder_icon_id()


def invalidate(obj) -> None:
    """Marca la miniatura del objeto como no válida (se recapturará)."""
    if obj is not None:
        _captured.discard(_key(obj))


# --- Captura (solo GUI) -------------------------------------------------------

def _find_view3d(context):
    """Devuelve (area, region WINDOW, space) de un Viewport 3D, o (None,None,None)."""
    area = context.area
    if area is not None and area.type == 'VIEW_3D':
        region = next((r for r in area.regions if r.type == 'WINDOW'), None)
        if region is not None:
            return area, region, area.spaces.active
    screen = context.screen
    if screen is not None:
        for a in screen.areas:
            if a.type == 'VIEW_3D':
                region = next((r for r in a.regions if r.type == 'WINDOW'), None)
                if region is not None:
                    return a, region, a.spaces.active
    return None, None, None


def _matrices(obj, rv3d, Matrix, Vector):
    """Matrices de vista y proyección: rotación actual del viewport + bbox del objeto."""
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    center = sum(corners, Vector((0.0, 0.0, 0.0))) / 8.0
    radius = max((c - center).length for c in corners) or 1.0
    radius *= 1.1  # pequeño margen alrededor del objeto

    rot = rv3d.view_rotation.to_matrix().to_4x4()
    forward = rot.to_3x3() @ Vector((0.0, 0.0, 1.0))  # +Z local = hacia la cámara
    dist = radius * 3.0
    eye = center + forward * dist
    view_matrix = (Matrix.Translation(eye) @ rot).inverted()

    near = max(dist - radius * 2.0, 0.001)
    far = dist + radius * 2.0
    r = radius
    proj = Matrix((
        (1.0 / r, 0.0, 0.0, 0.0),
        (0.0, 1.0 / r, 0.0, 0.0),
        (0.0, 0.0, -2.0 / (far - near), -(far + near) / (far - near)),
        (0.0, 0.0, 0.0, 1.0),
    ))
    return view_matrix, proj


def _render_into(context, space, region, obj, gpu, np, Matrix, Vector) -> bool:
    """Renderiza `obj` a un offscreen y guarda los píxeles en su preview."""
    view_matrix, proj = _matrices(obj, space.region_3d, Matrix, Vector)
    offscreen = gpu.types.GPUOffScreen(_THUMB_SIZE, _THUMB_SIZE)
    try:
        offscreen.draw_view3d(
            context.scene,
            context.view_layer,
            space,
            region,
            view_matrix,
            proj,
            do_color_management=True,
        )
        with offscreen.bind():
            framebuffer = gpu.state.active_framebuffer_get()
            # Leer en el formato NATIVO del offscreen (RGBA8 = 'UBYTE'). Leer
            # como 'FLOAT' fuerza una conversión interna que en Blender 5.x
            # devuelve datos corruptos. Con 'UBYTE' obtenemos los bytes tal
            # cual y normalizamos a [0, 1] aquí.
            buffer = framebuffer.read_color(
                0, 0, _THUMB_SIZE, _THUMB_SIZE, 4, 0, 'UBYTE')
    finally:
        offscreen.free()

    # read_color devuelve un Buffer multidimensional [alto][ancho][4]. Pasar
    # eso directo a np.array lo interpreta mal y produce ruido: hay que
    # aplanarlo a 1D con .dimensions antes de convertirlo.
    buffer.dimensions = _THUMB_SIZE * _THUMB_SIZE * 4
    pixels = np.array(buffer, dtype=np.float32) / 255.0
    pixels = pixels.reshape(-1, 4)
    # draw_view3d deja el alfa en 0 aunque el color RGB sea correcto; sin esto
    # el icono mostraría el damero de transparencia en vez del modelo.
    pixels[:, 3] = 1.0
    pixels = pixels.reshape(-1)
    key = _key(obj)
    preview = _previews.get(key) or _previews.new(key)
    preview.image_size = (_THUMB_SIZE, _THUMB_SIZE)
    _set_pixels(preview, pixels)
    _captured.add(key)
    return True


def _do_captures(context, objs) -> int:
    """Captura miniaturas de `objs` aislando cada uno. Devuelve cuántas logró.

    No hace nada sin GPU (background). Aísla ocultando el resto de la escena,
    fuerza modo Objeto durante la captura y restaura visibilidad, activo y modo.
    """
    if _previews is None or bpy.app.background:
        return 0
    targets = [o for o in objs if o is not None and o.type == 'MESH']
    if not targets:
        return 0
    try:
        import gpu
        import numpy as np
        from mathutils import Matrix, Vector
    except Exception:
        return 0

    area, region, space = _find_view3d(context)
    if region is None:
        return 0

    view_layer = context.view_layer
    active = view_layer.objects.active
    was_sculpt = context.mode == 'SCULPT'
    if was_sculpt and context.object is not None:
        bpy.ops.object.mode_set(mode='OBJECT')

    view_objs = list(view_layer.objects)
    snapshot = {o: o.hide_get() for o in view_objs}
    count = 0
    try:
        for target in targets:
            for o in view_objs:
                o.hide_set(o is not target)
            view_layer.update()
            try:
                if _render_into(context, space, region, target,
                                gpu, np, Matrix, Vector):
                    count += 1
            except Exception:
                pass  # una miniatura fallida no debe romper el resto
    finally:
        for o, hidden in snapshot.items():
            o.hide_set(hidden)
        view_layer.update()
        if active is not None:
            view_layer.objects.active = active
        if was_sculpt and context.object is not None:
            bpy.ops.object.mode_set(mode='SCULPT')
        if area is not None:
            area.tag_redraw()
    return count


def capture(context, obj) -> bool:
    """Captura (o recaptura) la miniatura de un único subtool."""
    return _do_captures(context, [obj]) > 0


def _auto_on() -> bool:
    from . import utils
    prefs = utils.get_prefs()
    return (getattr(prefs, "auto_thumbnails", True)
            and getattr(prefs, "show_thumbnails", True))


def maybe_capture(context, obj) -> None:
    """Captura solo si la preferencia de miniaturas automáticas está activa."""
    if _auto_on():
        capture(context, obj)


def maybe_capture_many(context, objs) -> None:
    """Como maybe_capture, para varios objetos en una sola pasada de aislamiento."""
    if _auto_on():
        _do_captures(context, objs)


# --- Operador de refresco -----------------------------------------------------

class SCULPTEXT_OT_subtool_thumbnails_refresh(bpy.types.Operator):
    """Regenera las miniaturas de todos los subtools del Tool activo"""

    bl_idname = "sculpt_ext.subtool_thumbnails_refresh"
    bl_label = "Refrescar miniaturas"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.type == 'MESH'

    def execute(self, context):
        if bpy.app.background:
            self.report({'WARNING'}, "Las miniaturas necesitan GPU (no en background)")
            return {'CANCELLED'}
        from . import utils
        root = utils.get_tool_root(context.object)
        subs = utils.all_subtools(root)
        done = _do_captures(context, subs)
        if done == 0:
            self.report({'WARNING'}, "No se pudo generar ninguna miniatura")
            return {'CANCELLED'}
        self.report({'INFO'}, f"{done} miniaturas actualizadas")
        return {'FINISHED'}


classes = (
    SCULPTEXT_OT_subtool_thumbnails_refresh,
)


def register():
    global _previews
    import bpy.utils.previews
    _previews = bpy.utils.previews.new()
    _captured.clear()
    _build_placeholder()
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    global _previews
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if _previews is not None:
        bpy.utils.previews.remove(_previews)
        _previews = None
    _captured.clear()
