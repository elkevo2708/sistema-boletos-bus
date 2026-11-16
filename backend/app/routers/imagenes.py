"""Subida autenticada y lectura pública de imágenes guardadas en MySQL."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencias import exigir_panel, obtener_sesion
from app.imagenes import ImagenInvalida, insertar_imagen, leer_imagen, validar_imagen

router = APIRouter()


def _error(exc: ImagenInvalida) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))


@router.post("/admin/imagenes", status_code=201)
async def subir_imagen(
    archivo: UploadFile = File(),
    _: dict = Depends(exigir_panel),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    contenido = await archivo.read()
    try:
        mime = validar_imagen(contenido, archivo.content_type)
    except ImagenInvalida as exc:
        raise _error(exc) from exc
    datos = await insertar_imagen(sesion, archivo.filename, mime, contenido)
    await sesion.commit()
    return {
        "id": datos["id"],
        "nombre": datos["nombre"],
        "tipo_mime": datos["tipo_mime"],
        "tamano": datos["tamano"],
        "url": datos["url"],
    }


@router.get("/medios/bd/{imagen_id}")
async def servir_imagen(imagen_id: int, sesion: AsyncSession = Depends(obtener_sesion)):
    fila = await leer_imagen(sesion, imagen_id)
    if fila is None:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    nombre = str(fila["nombre"]).replace('"', "")
    return Response(
        content=fila["contenido"],
        media_type=fila["tipo_mime"],
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "Content-Disposition": f'inline; filename="{nombre}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
