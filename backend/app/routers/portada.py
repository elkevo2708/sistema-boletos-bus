"""Diapositivas de la portada: imagen o video, en el sitio y en taquilla."""

import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencias import exigir_admin, obtener_sesion
from app.errores import traducir_error_mysql
from app.esquemas import PortadaIn

router = APIRouter()
MEDIOS = Path("/app/medios")
IMAGENES = {".jpg": ".jpg", ".jpeg": ".jpg", ".png": ".png", ".webp": ".webp"}
VIDEOS = {".mp4": ".mp4", ".webm": ".webm"}
TOPE_IMAGEN = 5 * 1024 * 1024
TOPE_VIDEO = 20 * 1024 * 1024
_YOUTUBE = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([\w-]{6,})")
_VIMEO = re.compile(r"vimeo\.com/(?:video/)?(\d+)")


def incrustar(enlace: str) -> str | None:
    youtube = _YOUTUBE.search(enlace)
    if youtube:
        video = youtube.group(1)
        return (
            f"https://www.youtube-nocookie.com/embed/{video}"
            f"?autoplay=1&mute=1&loop=1&playlist={video}&controls=0&playsinline=1&rel=0"
        )
    vimeo = _VIMEO.search(enlace)
    if vimeo:
        return f"https://player.vimeo.com/video/{vimeo.group(1)}?autoplay=1&muted=1&loop=1&background=1"
    return None


def publicar(fila: dict, completo: bool = False) -> dict:
    enlace = (fila.get("enlace") or "").strip()
    if fila["origen"] == "archivo" and fila.get("archivo"):
        url = f"/medios/{fila['archivo']}"
    else:
        url = enlace
    poster = f"/medios/{fila['poster']}" if fila.get("poster") else "/bus-lamana.jpg"
    datos = {
        "id": fila["id"],
        "tipo": fila["tipo"],
        "url": url,
        "incrustado": incrustar(enlace) if fila["tipo"] == "video" else None,
        "poster": poster,
        "titulo": fila["titulo"],
        "subtitulo": fila.get("subtitulo") or "",
        "texto_boton": fila.get("texto_boton") or "",
        "enlace_boton": fila.get("enlace_boton") or "",
        "orden": fila["orden"],
        "ambito": fila.get("ambito") or "portal",
    }
    if completo:
        datos.update(
            {
                "origen": fila["origen"],
                "enlace": enlace,
                "activo": bool(fila["activo"]),
            }
        )
    return datos


def _guardar(contenido: bytes, extension: str) -> str:
    from secrets import token_hex

    MEDIOS.mkdir(parents=True, exist_ok=True)
    nombre = f"{token_hex(8)}{extension}"
    (MEDIOS / nombre).write_bytes(contenido)
    return nombre


async def _leer_archivo(archivo: UploadFile, videos: bool) -> str:
    sufijo = Path(archivo.filename or "").suffix.lower()
    tabla = {**IMAGENES, **VIDEOS} if videos else IMAGENES
    extension = tabla.get(sufijo)
    if extension is None:
        detalle = "Suba un MP4, WebM, JPG, PNG o WebP" if videos else "El póster debe ser JPG, PNG o WebP"
        raise HTTPException(status_code=422, detail=detalle)
    contenido = await archivo.read()
    tope = TOPE_VIDEO if extension in VIDEOS.values() else TOPE_IMAGEN
    if not contenido or len(contenido) > tope:
        raise HTTPException(status_code=422, detail="El archivo supera el tamaño permitido")
    return _guardar(contenido, extension)


@router.get("/portada")
async def publica(ambito: str | None = None, sesion: AsyncSession = Depends(obtener_sesion)):
    if ambito is not None and ambito not in ("portal", "transporte"):
        raise HTTPException(status_code=422, detail="El ámbito es portal o transporte")
    sql = "SELECT * FROM portada WHERE activo = 1"
    parametros: dict = {}
    if ambito:
        sql += " AND ambito = :ambito"
        parametros["ambito"] = ambito
    sql += " ORDER BY orden, id"
    filas = (await sesion.execute(text(sql), parametros)).mappings().all()
    return [publicar(dict(fila)) for fila in filas]


@router.get("/admin/portada")
async def listar(_: dict = Depends(exigir_admin), sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (await sesion.execute(text("SELECT * FROM portada ORDER BY orden, id"))).mappings().all()
    return [publicar(dict(fila), completo=True) for fila in filas]


@router.post("/admin/portada", status_code=201)
async def crear(
    tipo: str = Form(),
    origen: str = Form(),
    titulo: str = Form(),
    subtitulo: str = Form(default=""),
    texto_boton: str = Form(default=""),
    enlace_boton: str = Form(default=""),
    enlace: str = Form(default=""),
    orden: int = Form(default=0),
    activo: str = Form(default="1"),
    ambito: str = Form(default="portal"),
    archivo: UploadFile | None = File(default=None),
    poster: UploadFile | None = File(default=None),
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    datos = _validar(tipo, origen, titulo, subtitulo, texto_boton, enlace_boton, enlace, orden, activo, ambito)
    nombre = None
    nombre_poster = None
    if datos["origen"] == "archivo":
        if archivo is None:
            raise HTTPException(status_code=422, detail="Falta el archivo de la diapositiva")
        nombre = await _leer_archivo(archivo, videos=datos["tipo"] == "video")
        if datos["tipo"] == "imagen" and Path(nombre).suffix.lower() in VIDEOS.values():
            raise HTTPException(status_code=422, detail="Una diapositiva de imagen no acepta video")
        if datos["tipo"] == "video" and Path(nombre).suffix.lower() not in VIDEOS.values():
            raise HTTPException(status_code=422, detail="Suba un video MP4 o WebM")
    if poster is not None and poster.filename:
        nombre_poster = await _leer_archivo(poster, videos=False)
    try:
        resultado = await sesion.execute(
            text(
                """
                INSERT INTO portada
                  (tipo, origen, archivo, enlace, poster, titulo, subtitulo, texto_boton, enlace_boton, orden, activo, ambito)
                VALUES
                  (:tipo, :origen, :archivo, :enlace, :poster, :titulo, :subtitulo, :texto_boton, :enlace_boton, :orden, :activo, :ambito)
                """
            ),
            {**datos, "archivo": nombre, "poster": nombre_poster},
        )
        await sesion.commit()
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)
    fila = (await sesion.execute(text("SELECT * FROM portada WHERE id = :id"), {"id": resultado.lastrowid})).mappings().one()
    return publicar(dict(fila), completo=True)


@router.patch("/admin/portada/{diapositiva_id}")
async def actualizar(
    diapositiva_id: int,
    datos: PortadaIn,
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    existe = (await sesion.execute(text("SELECT id FROM portada WHERE id = :id"), {"id": diapositiva_id})).first()
    if existe is None:
        raise HTTPException(status_code=404, detail="Diapositiva no encontrada")
    await sesion.execute(
        text(
            """
            UPDATE portada
               SET titulo = :titulo,
                   subtitulo = :subtitulo,
                   texto_boton = :texto_boton,
                   enlace_boton = :enlace_boton,
                   enlace = COALESCE(:enlace, enlace),
                   orden = :orden,
                   activo = :activo,
                   ambito = COALESCE(:ambito, ambito)
             WHERE id = :id
            """
        ),
        {
            "id": diapositiva_id,
            "titulo": datos.titulo.strip(),
            "subtitulo": (datos.subtitulo or "").strip(),
            "texto_boton": (datos.texto_boton or "").strip() or None,
            "enlace_boton": (datos.enlace_boton or "").strip() or None,
            "enlace": (datos.enlace or "").strip() or None,
            "orden": datos.orden,
            "activo": 1 if datos.activo else 0,
            "ambito": datos.ambito,
        },
    )
    await sesion.commit()
    fila = (await sesion.execute(text("SELECT * FROM portada WHERE id = :id"), {"id": diapositiva_id})).mappings().one()
    return publicar(dict(fila), completo=True)


@router.delete("/admin/portada/{diapositiva_id}", status_code=204)
async def eliminar(
    diapositiva_id: int,
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    resultado = await sesion.execute(text("DELETE FROM portada WHERE id = :id"), {"id": diapositiva_id})
    if resultado.rowcount == 0:
        raise HTTPException(status_code=404, detail="Diapositiva no encontrada")
    await sesion.commit()


def _validar(tipo, origen, titulo, subtitulo, texto_boton, enlace_boton, enlace, orden, activo, ambito="portal") -> dict:
    if tipo not in ("imagen", "video"):
        raise HTTPException(status_code=422, detail="El tipo es imagen o video")
    if origen not in ("archivo", "enlace"):
        raise HTTPException(status_code=422, detail="El origen es archivo o enlace")
    titulo = titulo.strip()
    if len(titulo) < 3 or len(titulo) > 160:
        raise HTTPException(status_code=422, detail="El título debe tener entre 3 y 160 caracteres")
    enlace = enlace.strip()
    if origen == "enlace" and not enlace:
        raise HTTPException(status_code=422, detail="Falta el enlace de la imagen o del video")
    if tipo == "video" and origen == "enlace" and not (incrustar(enlace) or enlace.lower().endswith((".mp4", ".webm"))):
        raise HTTPException(status_code=422, detail="Use un enlace de YouTube, Vimeo, MP4 o WebM")
    if ambito not in ("portal", "transporte"):
        raise HTTPException(status_code=422, detail="El ámbito es portal o transporte")
    return {
        "tipo": tipo,
        "origen": origen,
        "titulo": titulo,
        "subtitulo": subtitulo.strip()[:300],
        "texto_boton": texto_boton.strip()[:80] or None,
        "enlace_boton": enlace_boton.strip()[:300] or None,
        "enlace": enlace or None,
        "orden": orden,
        "activo": 1 if str(activo).lower() in {"1", "true", "si", "sí"} else 0,
        "ambito": ambito,
    }
