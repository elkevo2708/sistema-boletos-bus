import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencias import exigir_transporte, obtener_sesion
from app.errores import traducir_error_mysql
from app.esquemas import AnuncioIn, BlogIn
from app.presentacion import fila_a_dict
from app.slug import slugificar

router = APIRouter(dependencies=[Depends(exigir_transporte)])
MEDIOS = Path("/app/medios")
TIPOS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
TOPE = 5 * 1024 * 1024


def _publicar(fila: dict) -> dict:
    for campo in ("imagen", "archivo"):
        valor = fila.get(campo)
        if valor and not str(valor).startswith("/medios/"):
            if campo == "archivo":
                fila["url"] = f"/medios/{valor}"
            else:
                fila[campo] = f"/medios/{valor}"
    if fila.get("archivo") and "url" not in fila:
        fila["url"] = f"/medios/{fila['archivo']}"
    return fila


def _nombre_archivo(valor: str | None) -> str | None:
    if not valor:
        return None
    limpio = str(valor).strip().lstrip("/")
    if limpio.startswith("medios/"):
        limpio = limpio[len("medios/") :]
    return limpio or None


async def _guardar_upload(archivo: UploadFile) -> str:
    from secrets import token_hex

    extension = TIPOS.get(archivo.content_type or "")
    if extension is None and archivo.filename:
        sufijo = Path(archivo.filename).suffix.lower()
        extension = {".jpg": ".jpg", ".jpeg": ".jpg", ".png": ".png", ".webp": ".webp"}.get(sufijo)
    if extension is None:
        raise HTTPException(status_code=422, detail="Solo se aceptan imágenes JPG, PNG o WebP")
    contenido = await archivo.read()
    if not contenido or len(contenido) > TOPE:
        raise HTTPException(status_code=422, detail="La imagen debe pesar entre 1 byte y 5 MB")
    nombre = f"{token_hex(8)}{extension}"
    MEDIOS.mkdir(parents=True, exist_ok=True)
    (MEDIOS / nombre).write_bytes(contenido)
    return nombre


async def _slug_libre(sesion: AsyncSession, titulo: str, propio: int | None = None) -> str:
    base = slugificar(titulo)
    for indice in range(1, 20):
        candidato = base if indice == 1 else f"{base}-{indice}"
        existe = (
            await sesion.execute(
                text("SELECT id FROM blog_posts WHERE slug = :slug AND (:propio IS NULL OR id <> :propio)"),
                {"slug": candidato, "propio": propio},
            )
        ).first()
        if existe is None:
            return candidato
    raise HTTPException(status_code=409, detail="No se pudo generar un enlace único")


@router.get("/blog")
async def admin_blog(sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT id, slug, titulo, resumen, cuerpo, categoria, imagen, publicado, publicado_en
                  FROM blog_posts
                 ORDER BY publicado_en DESC
                """
            )
        )
    ).mappings().all()
    return [_publicar(fila_a_dict(fila)) for fila in filas]


@router.post("/blog", status_code=201)
async def crear_post(datos: BlogIn, sesion: AsyncSession = Depends(obtener_sesion)):
    slug = await _slug_libre(sesion, datos.titulo)
    try:
        resultado = await sesion.execute(
            text(
                """
                INSERT INTO blog_posts (slug, titulo, resumen, cuerpo, categoria, imagen, publicado, publicado_en)
                VALUES (:slug, :titulo, :resumen, :cuerpo, :categoria, :imagen, :publicado, :publicado_en)
                """
            ),
            {
                "slug": slug,
                "titulo": datos.titulo,
                "resumen": datos.resumen,
                "cuerpo": datos.cuerpo,
                "categoria": datos.categoria,
                "imagen": datos.imagen,
                "publicado": int(datos.publicado),
                "publicado_en": datos.publicado_en,
            },
        )
        await sesion.commit()
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)
    return {"id": resultado.lastrowid, "slug": slug}


@router.patch("/blog/{post_id}")
async def editar_post(post_id: int, datos: BlogIn, sesion: AsyncSession = Depends(obtener_sesion)):
    slug = await _slug_libre(sesion, datos.titulo, propio=post_id)
    resultado = await sesion.execute(
        text(
            """
            UPDATE blog_posts
               SET slug = :slug,
                   titulo = :titulo,
                   resumen = :resumen,
                   cuerpo = :cuerpo,
                   categoria = :categoria,
                   imagen = :imagen,
                   publicado = :publicado,
                   publicado_en = :publicado_en
             WHERE id = :id
            """
        ),
        {
            "id": post_id,
            "slug": slug,
            "titulo": datos.titulo,
            "resumen": datos.resumen,
            "cuerpo": datos.cuerpo,
            "categoria": datos.categoria,
            "imagen": datos.imagen,
            "publicado": int(datos.publicado),
            "publicado_en": datos.publicado_en,
        },
    )
    if resultado.rowcount == 0:
        await sesion.rollback()
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    await sesion.commit()
    return {"id": post_id, "slug": slug}


@router.delete("/blog/{post_id}", status_code=204)
async def borrar_post(post_id: int, sesion: AsyncSession = Depends(obtener_sesion)):
    resultado = await sesion.execute(text("DELETE FROM blog_posts WHERE id = :id"), {"id": post_id})
    if resultado.rowcount == 0:
        await sesion.rollback()
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    await sesion.commit()


@router.get("/anuncios")
async def admin_anuncios(sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT id, titulo, mensaje, enlace, texto_boton, formato, imagen, tipo, activo, inicio, fin
                  FROM anuncios
                 ORDER BY inicio DESC, id DESC
                """
            )
        )
    ).mappings().all()
    return [_publicar(fila_a_dict(fila)) for fila in filas]


def _anuncio_modelo(**campos) -> AnuncioIn:
    try:
        return AnuncioIn(**campos)
    except Exception as exc:
        errores = getattr(exc, "errors", None)
        if callable(errores):
            mensajes = [item.get("msg", "Dato inválido").removeprefix("Value error, ") for item in errores()]
            raise HTTPException(status_code=422, detail=". ".join(mensajes) or "Dato inválido") from exc
        raise HTTPException(status_code=422, detail=str(exc)) from exc


async def _persistir_anuncio(
    sesion: AsyncSession,
    datos: AnuncioIn,
    imagen: UploadFile | None,
    anuncio_id: int | None,
) -> dict:
    previa = None
    if anuncio_id is not None:
        previa = (
            await sesion.execute(text("SELECT imagen FROM anuncios WHERE id = :id"), {"id": anuncio_id})
        ).mappings().first()
        if previa is None:
            raise HTTPException(status_code=404, detail="Anuncio no encontrado")
    nombre = _nombre_archivo(previa["imagen"]) if previa else None
    nuevo = None
    if datos.formato == "imagen":
        if imagen is not None and imagen.filename:
            nuevo = await _guardar_upload(imagen)
            nombre = nuevo
        if not nombre:
            raise HTTPException(status_code=422, detail="La promoción con imagen necesita un archivo")
    else:
        nombre = None
    valores = {
        "titulo": datos.titulo,
        "mensaje": datos.mensaje or None,
        "enlace": datos.enlace,
        "texto_boton": datos.texto_boton,
        "formato": datos.formato,
        "imagen": nombre,
        "tipo": datos.tipo,
        "activo": int(datos.activo),
        "inicio": datos.inicio,
        "fin": datos.fin,
    }
    try:
        if anuncio_id is None:
            resultado = await sesion.execute(
                text(
                    """
                    INSERT INTO anuncios (
                      titulo, mensaje, enlace, texto_boton, formato, imagen, tipo, activo, inicio, fin
                    ) VALUES (
                      :titulo, :mensaje, :enlace, :texto_boton, :formato, :imagen, :tipo, :activo, :inicio, :fin
                    )
                    """
                ),
                valores,
            )
            guardado = int(resultado.lastrowid)
        else:
            valores["id"] = anuncio_id
            await sesion.execute(
                text(
                    """
                    UPDATE anuncios
                       SET titulo = :titulo, mensaje = :mensaje, enlace = :enlace,
                           texto_boton = :texto_boton, formato = :formato, imagen = :imagen,
                           tipo = :tipo, activo = :activo, inicio = :inicio, fin = :fin
                     WHERE id = :id
                    """
                ),
                valores,
            )
            guardado = anuncio_id
        await sesion.commit()
    except HTTPException:
        if nuevo:
            (MEDIOS / nuevo).unlink(missing_ok=True)
        raise
    except SQLAlchemyError as exc:
        if nuevo:
            (MEDIOS / nuevo).unlink(missing_ok=True)
        await sesion.rollback()
        traducir_error_mysql(exc)
    anterior = _nombre_archivo(previa["imagen"]) if previa else None
    if nuevo and anterior and anterior != nuevo and re.fullmatch(r"[0-9a-f]{16}\.(jpg|png|webp)", anterior):
        (MEDIOS / anterior).unlink(missing_ok=True)
    return {"id": guardado, "formato": datos.formato, "imagen": f"/medios/{nombre}" if nombre else None}


@router.post("/anuncios", status_code=201)
async def crear_anuncio(
    titulo: str = Form(),
    mensaje: str = Form(default=""),
    enlace: str = Form(default=""),
    texto_boton: str = Form(default=""),
    tipo: str = Form(default="modal"),
    formato: str = Form(default="texto"),
    activo: str = Form(default="true"),
    inicio: str = Form(),
    fin: str = Form(),
    imagen: UploadFile | None = File(default=None),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    datos = _anuncio_modelo(
        titulo=titulo,
        mensaje=mensaje,
        enlace=enlace,
        texto_boton=texto_boton,
        tipo=tipo,
        formato=formato,
        activo=activo,
        inicio=inicio,
        fin=fin,
    )
    return await _persistir_anuncio(sesion, datos, imagen, None)


@router.patch("/anuncios/{anuncio_id}")
async def editar_anuncio(
    anuncio_id: int,
    titulo: str = Form(),
    mensaje: str = Form(default=""),
    enlace: str = Form(default=""),
    texto_boton: str = Form(default=""),
    tipo: str = Form(default="modal"),
    formato: str = Form(default="texto"),
    activo: str = Form(default="true"),
    inicio: str = Form(),
    fin: str = Form(),
    imagen: UploadFile | None = File(default=None),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    datos = _anuncio_modelo(
        titulo=titulo,
        mensaje=mensaje,
        enlace=enlace,
        texto_boton=texto_boton,
        tipo=tipo,
        formato=formato,
        activo=activo,
        inicio=inicio,
        fin=fin,
    )
    return await _persistir_anuncio(sesion, datos, imagen, anuncio_id)


@router.delete("/anuncios/{anuncio_id}", status_code=204)
async def borrar_anuncio(anuncio_id: int, sesion: AsyncSession = Depends(obtener_sesion)):
    resultado = await sesion.execute(text("DELETE FROM anuncios WHERE id = :id"), {"id": anuncio_id})
    if resultado.rowcount == 0:
        await sesion.rollback()
        raise HTTPException(status_code=404, detail="Anuncio no encontrado")
    await sesion.commit()


@router.get("/galeria")
async def admin_galeria(sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text("SELECT id, titulo, descripcion, categoria, archivo FROM galeria ORDER BY id DESC")
        )
    ).mappings().all()
    return [_publicar(fila_a_dict(fila)) for fila in filas]


@router.post("/galeria", status_code=201)
async def subir_imagen(
    titulo: str = Form(min_length=2, max_length=140),
    categoria: str = Form(),
    descripcion: str = Form(default=""),
    archivo: UploadFile = File(),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    if categoria not in ("buses", "destinos", "terminales"):
        raise HTTPException(status_code=422, detail="Categoría de galería no válida")
    extension = TIPOS.get(archivo.content_type or "")
    if extension is None and archivo.filename:
        sufijo = Path(archivo.filename).suffix.lower()
        extension = {".jpg": ".jpg", ".jpeg": ".jpg", ".png": ".png", ".webp": ".webp"}.get(sufijo)
    if extension is None:
        raise HTTPException(status_code=422, detail="Solo se aceptan imágenes JPG, PNG o WebP")
    contenido = await archivo.read()
    if not contenido or len(contenido) > TOPE:
        raise HTTPException(status_code=422, detail="La imagen debe pesar entre 1 byte y 5 MB")
    from secrets import token_hex

    nombre = f"{token_hex(8)}{extension}"
    MEDIOS.mkdir(parents=True, exist_ok=True)
    (MEDIOS / nombre).write_bytes(contenido)
    try:
        resultado = await sesion.execute(
            text(
                """
                INSERT INTO galeria (titulo, descripcion, categoria, archivo)
                VALUES (:titulo, :descripcion, :categoria, :archivo)
                """
            ),
            {
                "titulo": titulo.strip(),
                "descripcion": descripcion.strip() or None,
                "categoria": categoria,
                "archivo": nombre,
            },
        )
        await sesion.commit()
    except SQLAlchemyError as exc:
        (MEDIOS / nombre).unlink(missing_ok=True)
        await sesion.rollback()
        traducir_error_mysql(exc)
    return {"id": resultado.lastrowid, "archivo": nombre, "url": f"/medios/{nombre}"}


@router.delete("/galeria/{imagen_id}", status_code=204)
async def borrar_imagen(imagen_id: int, sesion: AsyncSession = Depends(obtener_sesion)):
    fila = (
        await sesion.execute(text("SELECT archivo FROM galeria WHERE id = :id"), {"id": imagen_id})
    ).mappings().first()
    if fila is None:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    await sesion.execute(text("DELETE FROM galeria WHERE id = :id"), {"id": imagen_id})
    await sesion.commit()
    if re.fullmatch(r"[0-9a-f]{16}\.(jpg|png|webp)", fila["archivo"] or ""):
        (MEDIOS / fila["archivo"]).unlink(missing_ok=True)
