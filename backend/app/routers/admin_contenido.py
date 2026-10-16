import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencias import exigir_admin, obtener_sesion
from app.errores import traducir_error_mysql
from app.esquemas import AnuncioIn, BlogIn
from app.presentacion import fila_a_dict
from app.slug import slugificar

router = APIRouter(dependencies=[Depends(exigir_admin)])
MEDIOS = Path("/app/medios")
TIPOS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
TOPE = 5 * 1024 * 1024


def _publicar(fila: dict) -> dict:
    if fila.get("imagen"):
        fila["imagen"] = f"/medios/{fila['imagen']}"
    if fila.get("archivo"):
        fila["url"] = f"/medios/{fila['archivo']}"
    return fila


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
                SELECT id, titulo, mensaje, enlace, tipo, activo, inicio, fin
                  FROM anuncios
                 ORDER BY inicio DESC, id DESC
                """
            )
        )
    ).mappings().all()
    return [fila_a_dict(fila) for fila in filas]


@router.post("/anuncios", status_code=201)
async def crear_anuncio(datos: AnuncioIn, sesion: AsyncSession = Depends(obtener_sesion)):
    if datos.fin < datos.inicio:
        raise HTTPException(status_code=422, detail="La fecha final no puede ser anterior al inicio")
    resultado = await sesion.execute(
        text(
            """
            INSERT INTO anuncios (titulo, mensaje, enlace, tipo, activo, inicio, fin)
            VALUES (:titulo, :mensaje, :enlace, :tipo, :activo, :inicio, :fin)
            """
        ),
        {
            "titulo": datos.titulo,
            "mensaje": datos.mensaje,
            "enlace": datos.enlace,
            "tipo": datos.tipo,
            "activo": int(datos.activo),
            "inicio": datos.inicio,
            "fin": datos.fin,
        },
    )
    await sesion.commit()
    return {"id": resultado.lastrowid}


@router.patch("/anuncios/{anuncio_id}")
async def editar_anuncio(anuncio_id: int, datos: AnuncioIn, sesion: AsyncSession = Depends(obtener_sesion)):
    if datos.fin < datos.inicio:
        raise HTTPException(status_code=422, detail="La fecha final no puede ser anterior al inicio")
    resultado = await sesion.execute(
        text(
            """
            UPDATE anuncios
               SET titulo = :titulo, mensaje = :mensaje, enlace = :enlace,
                   tipo = :tipo, activo = :activo, inicio = :inicio, fin = :fin
             WHERE id = :id
            """
        ),
        {
            "id": anuncio_id,
            "titulo": datos.titulo,
            "mensaje": datos.mensaje,
            "enlace": datos.enlace,
            "tipo": datos.tipo,
            "activo": int(datos.activo),
            "inicio": datos.inicio,
            "fin": datos.fin,
        },
    )
    if resultado.rowcount == 0:
        await sesion.rollback()
        raise HTTPException(status_code=404, detail="Anuncio no encontrado")
    await sesion.commit()
    return {"id": anuncio_id}


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
