from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencias import obtener_sesion
from app.presentacion import fila_a_dict

router = APIRouter()


def _con_medios(fila: dict, campo: str = "imagen") -> dict:
    if fila.get(campo):
        fila[campo] = f"/medios/{fila[campo]}"
    return fila


@router.get("/blog")
async def listar_blog(
    categoria: str | None = Query(default=None),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    if categoria and categoria not in ("noticia", "destino"):
        raise HTTPException(status_code=422, detail="La categoría debe ser noticia o destino")
    filas = (
        await sesion.execute(
            text(
                """
                SELECT id, slug, titulo, resumen, categoria, imagen, publicado_en
                  FROM blog_posts
                 WHERE publicado = 1
                   AND (:categoria IS NULL OR categoria = :categoria)
                 ORDER BY publicado_en DESC
                """
            ),
            {"categoria": categoria},
        )
    ).mappings().all()
    return [_con_medios(fila_a_dict(fila)) for fila in filas]


@router.get("/blog/{slug}")
async def detalle_blog(slug: str, sesion: AsyncSession = Depends(obtener_sesion)):
    fila = (
        await sesion.execute(
            text(
                """
                SELECT id, slug, titulo, resumen, cuerpo, categoria, imagen, publicado_en
                  FROM blog_posts
                 WHERE slug = :slug AND publicado = 1
                """
            ),
            {"slug": slug},
        )
    ).mappings().first()
    if fila is None:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    return _con_medios(fila_a_dict(fila))


@router.get("/anuncios")
async def anuncios_vigentes(sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT id, titulo, mensaje, enlace, texto_boton, formato, imagen, tipo, inicio, fin
                  FROM anuncios
                 WHERE activo = 1
                   AND inicio <= CURDATE()
                   AND fin >= CURDATE()
                 ORDER BY tipo, id
                """
            )
        )
    ).mappings().all()
    return [_con_medios(fila_a_dict(fila)) for fila in filas]


@router.get("/galeria")
async def listar_galeria(
    categoria: str | None = Query(default=None),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    if categoria and categoria not in ("buses", "destinos", "terminales"):
        raise HTTPException(status_code=422, detail="Categoría de galería no válida")
    filas = (
        await sesion.execute(
            text(
                """
                SELECT id, titulo, descripcion, categoria, archivo
                  FROM galeria
                 WHERE :categoria IS NULL OR categoria = :categoria
                 ORDER BY categoria, id
                """
            ),
            {"categoria": categoria},
        )
    ).mappings().all()
    salida = []
    for fila in filas:
        item = fila_a_dict(fila)
        item["url"] = f"/medios/{item['archivo']}"
        salida.append(item)
    return salida
