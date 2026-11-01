"""Portal de turismo de La Maná. Las fichas se editan en taquilla."""

from pathlib import Path
from secrets import token_hex

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencias import exigir_turismo, obtener_sesion
from app.errores import traducir_error_mysql
from app.esquemas import TurismoCategoriaIn, TurismoContactoIn, TurismoEventoIn, TurismoFichaIn
from app.slug import slugificar

router = APIRouter()
MEDIOS = Path("/app/medios")
TIPOS_FICHA = ("atractivo", "gastronomia", "hospedaje", "actividad", "ruta", "parroquia", "guia", "emprendimiento", "directorio")
EXTENSIONES = {".jpg": ".jpg", ".jpeg": ".jpg", ".png": ".png", ".webp": ".webp"}


def _url(valor: str | None) -> str | None:
    if not valor:
        return None
    texto_url = str(valor).strip()
    if texto_url.startswith("/"):
        return texto_url
    return f"/medios/{texto_url}"


def _fila_ficha(fila: dict) -> dict:
    return {
        "id": fila["id"],
        "tipo": fila["tipo"],
        "categoria_id": fila["categoria_id"],
        "categoria": fila.get("categoria"),
        "nombre": fila["nombre"],
        "slug": fila["slug"],
        "resumen": fila["resumen"],
        "cuerpo": fila["cuerpo"],
        "zona": fila["zona"],
        "direccion": fila["direccion"],
        "lat": float(fila["lat"]) if fila["lat"] is not None else None,
        "lng": float(fila["lng"]) if fila["lng"] is not None else None,
        "imagen": _url(fila["imagen"]),
        "credito": fila["credito"],
        "destacado": bool(fila["destacado"]),
        "orden": fila["orden"],
        "activo": bool(fila["activo"]),
    }


def _fila_evento(fila: dict) -> dict:
    return {
        "id": fila["id"],
        "categoria_id": fila["categoria_id"],
        "categoria": fila.get("categoria"),
        "titulo": fila["titulo"],
        "slug": fila["slug"],
        "resumen": fila["resumen"],
        "cuerpo": fila["cuerpo"],
        "inicio": fila["inicio"].isoformat() if fila["inicio"] else None,
        "fin": fila["fin"].isoformat() if fila["fin"] else None,
        "lugar": fila["lugar"],
        "imagen": _url(fila["imagen"]),
        "credito": fila["credito"],
        "activo": bool(fila["activo"]),
    }


async def _slug_unico(
    sesion: AsyncSession,
    tabla: str,
    columna: str,
    base: str,
    propio: int | None,
    extra: str = "",
    extra_params: dict | None = None,
) -> str:
    for indice in range(1, 30):
        candidato = base if indice == 1 else f"{base}-{indice}"
        parametros = {"slug": candidato, "id": propio or 0, **(extra_params or {})}
        existe = (
            await sesion.execute(text(f"SELECT id FROM {tabla} WHERE {columna} = :slug AND id <> :id {extra}"), parametros)
        ).first()
        if existe is None:
            return candidato
    raise HTTPException(status_code=409, detail="No hay un slug libre para ese nombre")


@router.get("/turismo/resumen")
async def resumen(sesion: AsyncSession = Depends(obtener_sesion)):
    conteos = {}
    filas = (
        await sesion.execute(
            text("SELECT tipo, COUNT(*) AS total FROM turismo_fichas WHERE activo = 1 GROUP BY tipo")
        )
    ).mappings().all()
    for fila in filas:
        conteos[fila["tipo"]] = int(fila["total"])
    eventos = (
        await sesion.execute(text("SELECT COUNT(*) FROM turismo_eventos WHERE activo = 1"))
    ).scalar_one()
    conteos["evento"] = int(eventos)
    conteos["transporte"] = int((await sesion.execute(text("SELECT COUNT(*) FROM rutas"))).scalar_one())
    try:
        conteos["taxi"] = int(
            (await sesion.execute(text("SELECT COUNT(*) FROM taxi_conductores WHERE activo = 1 AND estado = 'disponible'"))).scalar_one()
        )
    except SQLAlchemyError:
        await sesion.rollback()
        conteos["taxi"] = 0
    destacados = (
        await sesion.execute(
            text(
                """
                SELECT f.*, c.nombre AS categoria
                  FROM turismo_fichas f
                  LEFT JOIN turismo_categorias c ON c.id = f.categoria_id
                 WHERE f.activo = 1 AND f.destacado = 1
                 ORDER BY f.orden, f.id
                 LIMIT 6
                """
            )
        )
    ).mappings().all()
    proximos = (
        await sesion.execute(
            text(
                """
                SELECT e.*, c.nombre AS categoria
                  FROM turismo_eventos e
                  LEFT JOIN turismo_categorias c ON c.id = e.categoria_id
                 WHERE e.activo = 1
                 ORDER BY e.inicio, e.id
                 LIMIT 3
                """
            )
        )
    ).mappings().all()
    return {
        "conteos": conteos,
        "destacados": [_fila_ficha(dict(fila)) for fila in destacados],
        "eventos": [_fila_evento(dict(fila)) for fila in proximos],
    }


@router.get("/turismo/categorias")
async def categorias(tipo: str | None = None, sesion: AsyncSession = Depends(obtener_sesion)):
    sql = "SELECT id, tipo, nombre, slug, resumen, orden FROM turismo_categorias WHERE activo = 1"
    parametros = {}
    if tipo:
        sql += " AND tipo = :tipo"
        parametros["tipo"] = tipo
    sql += " ORDER BY orden, nombre"
    filas = (await sesion.execute(text(sql), parametros)).mappings().all()
    return [dict(fila) for fila in filas]


@router.get("/turismo/fichas")
async def fichas(
    tipo: str | None = None,
    q: str | None = None,
    categoria: str | None = None,
    sesion: AsyncSession = Depends(obtener_sesion),
):
    sql = """
        SELECT f.*, c.nombre AS categoria
          FROM turismo_fichas f
          LEFT JOIN turismo_categorias c ON c.id = f.categoria_id
         WHERE f.activo = 1
    """
    parametros: dict = {}
    if tipo:
        if tipo not in TIPOS_FICHA:
            raise HTTPException(status_code=422, detail="Tipo de ficha no reconocido")
        sql += " AND f.tipo = :tipo"
        parametros["tipo"] = tipo
    if categoria:
        sql += " AND c.slug = :categoria"
        parametros["categoria"] = categoria
    if q and q.strip():
        sql += " AND (f.nombre LIKE :q OR f.resumen LIKE :q OR f.zona LIKE :q OR f.cuerpo LIKE :q)"
        parametros["q"] = f"%{q.strip()}%"
    sql += " ORDER BY f.orden, f.nombre"
    filas = (await sesion.execute(text(sql), parametros)).mappings().all()
    return [_fila_ficha(dict(fila)) for fila in filas]


@router.get("/turismo/fichas/{tipo}/{slug}")
async def ficha(tipo: str, slug: str, sesion: AsyncSession = Depends(obtener_sesion)):
    fila = (
        await sesion.execute(
            text(
                """
                SELECT f.*, c.nombre AS categoria
                  FROM turismo_fichas f
                  LEFT JOIN turismo_categorias c ON c.id = f.categoria_id
                 WHERE f.tipo = :tipo AND f.slug = :slug AND f.activo = 1
                """
            ),
            {"tipo": tipo, "slug": slug},
        )
    ).mappings().first()
    if fila is None:
        raise HTTPException(status_code=404, detail="Ficha no encontrada")
    return _fila_ficha(dict(fila))


@router.get("/turismo/eventos")
async def eventos(sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT e.*, c.nombre AS categoria
                  FROM turismo_eventos e
                  LEFT JOIN turismo_categorias c ON c.id = e.categoria_id
                 WHERE e.activo = 1
                 ORDER BY e.inicio, e.id
                """
            )
        )
    ).mappings().all()
    return [_fila_evento(dict(fila)) for fila in filas]


@router.get("/turismo/eventos/{slug}")
async def evento(slug: str, sesion: AsyncSession = Depends(obtener_sesion)):
    fila = (
        await sesion.execute(
            text(
                """
                SELECT e.*, c.nombre AS categoria
                  FROM turismo_eventos e
                  LEFT JOIN turismo_categorias c ON c.id = e.categoria_id
                 WHERE e.slug = :slug AND e.activo = 1
                """
            ),
            {"slug": slug},
        )
    ).mappings().first()
    if fila is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return _fila_evento(dict(fila))


@router.get("/turismo/galeria")
async def galeria(sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT id, titulo, descripcion, archivo, credito, orden
                  FROM turismo_galeria
                 WHERE activo = 1
                 ORDER BY orden, id
                """
            )
        )
    ).mappings().all()
    return [
        {
            "id": fila["id"],
            "titulo": fila["titulo"],
            "descripcion": fila["descripcion"],
            "url": _url(fila["archivo"]),
            "credito": fila["credito"],
            "orden": fila["orden"],
        }
        for fila in filas
    ]


@router.get("/turismo/mapa")
async def mapa(sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT tipo, nombre, slug, resumen, zona, lat, lng
                  FROM turismo_fichas
                 WHERE activo = 1 AND lat IS NOT NULL AND lng IS NOT NULL
                 ORDER BY orden, nombre
                """
            )
        )
    ).mappings().all()
    return [
        {
            "tipo": fila["tipo"],
            "nombre": fila["nombre"],
            "slug": fila["slug"],
            "resumen": fila["resumen"],
            "zona": fila["zona"],
            "lat": float(fila["lat"]),
            "lng": float(fila["lng"]),
        }
        for fila in filas
    ]


@router.post("/turismo/contacto", status_code=201)
async def contacto(datos: TurismoContactoIn, sesion: AsyncSession = Depends(obtener_sesion)):
    await sesion.execute(
        text(
            """
            INSERT INTO turismo_mensajes (nombre, email, mensaje)
            VALUES (:nombre, :email, :mensaje)
            """
        ),
        {"nombre": datos.nombre.strip(), "email": str(datos.email).lower(), "mensaje": datos.mensaje.strip()},
    )
    await sesion.commit()
    return {"estado": "recibido"}


@router.get("/admin/turismo/categorias")
async def admin_categorias(_: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(text("SELECT * FROM turismo_categorias ORDER BY tipo, orden, nombre"))
    ).mappings().all()
    return [dict(fila) for fila in filas]


@router.post("/admin/turismo/categorias", status_code=201)
async def crear_categoria(
    datos: TurismoCategoriaIn,
    _: dict = Depends(exigir_turismo),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    slug = await _slug_unico(
        sesion, "turismo_categorias", "slug", slugificar(datos.nombre), None, "AND tipo = :tipo", {"tipo": datos.tipo}
    )
    try:
        resultado = await sesion.execute(
            text(
                """
                INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden, activo)
                VALUES (:tipo, :nombre, :slug, :resumen, :orden, :activo)
                """
            ),
            {
                "tipo": datos.tipo,
                "nombre": datos.nombre.strip(),
                "slug": slug,
                "resumen": datos.resumen.strip()[:400],
                "orden": datos.orden,
                "activo": 1 if datos.activo else 0,
            },
        )
        await sesion.commit()
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)
    return {"id": resultado.lastrowid, "slug": slug}


@router.patch("/admin/turismo/categorias/{categoria_id}")
async def editar_categoria(
    categoria_id: int,
    datos: TurismoCategoriaIn,
    _: dict = Depends(exigir_turismo),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    await sesion.execute(
        text(
            """
            UPDATE turismo_categorias
               SET tipo = :tipo, nombre = :nombre, resumen = :resumen, orden = :orden, activo = :activo
             WHERE id = :id
            """
        ),
        {
            "id": categoria_id,
            "tipo": datos.tipo,
            "nombre": datos.nombre.strip(),
            "resumen": datos.resumen.strip()[:400],
            "orden": datos.orden,
            "activo": 1 if datos.activo else 0,
        },
    )
    await sesion.commit()
    return {"id": categoria_id}


@router.delete("/admin/turismo/categorias/{categoria_id}", status_code=204)
async def borrar_categoria(
    categoria_id: int,
    _: dict = Depends(exigir_turismo),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    resultado = await sesion.execute(text("DELETE FROM turismo_categorias WHERE id = :id"), {"id": categoria_id})
    if resultado.rowcount == 0:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    await sesion.commit()


@router.get("/admin/turismo/fichas")
async def admin_fichas(_: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT f.*, c.nombre AS categoria
                  FROM turismo_fichas f
                  LEFT JOIN turismo_categorias c ON c.id = f.categoria_id
                 ORDER BY f.tipo, f.orden, f.nombre
                """
            )
        )
    ).mappings().all()
    return [_fila_ficha(dict(fila)) for fila in filas]


@router.post("/admin/turismo/fichas", status_code=201)
async def crear_ficha(
    datos: TurismoFichaIn,
    _: dict = Depends(exigir_turismo),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    slug = await _slug_unico(
        sesion, "turismo_fichas", "slug", slugificar(datos.nombre), None, "AND tipo = :tipo", {"tipo": datos.tipo}
    )
    resultado = await _guardar_ficha(sesion, datos, slug, None)
    return {"id": resultado, "slug": slug}


@router.patch("/admin/turismo/fichas/{ficha_id}")
async def editar_ficha(
    ficha_id: int,
    datos: TurismoFichaIn,
    _: dict = Depends(exigir_turismo),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    actual = (await sesion.execute(text("SELECT slug FROM turismo_fichas WHERE id = :id"), {"id": ficha_id})).first()
    if actual is None:
        raise HTTPException(status_code=404, detail="Ficha no encontrada")
    await _guardar_ficha(sesion, datos, actual[0], ficha_id)
    return {"id": ficha_id, "slug": actual[0]}


@router.delete("/admin/turismo/fichas/{ficha_id}", status_code=204)
async def borrar_ficha(
    ficha_id: int,
    _: dict = Depends(exigir_turismo),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    resultado = await sesion.execute(text("DELETE FROM turismo_fichas WHERE id = :id"), {"id": ficha_id})
    if resultado.rowcount == 0:
        raise HTTPException(status_code=404, detail="Ficha no encontrada")
    await sesion.commit()


async def _guardar_ficha(sesion: AsyncSession, datos: TurismoFichaIn, slug: str, ficha_id: int | None) -> int:
    campos = {
        "tipo": datos.tipo,
        "categoria_id": datos.categoria_id,
        "nombre": datos.nombre.strip(),
        "slug": slug,
        "resumen": datos.resumen.strip(),
        "cuerpo": datos.cuerpo.strip(),
        "zona": datos.zona.strip()[:120],
        "direccion": datos.direccion.strip()[:200],
        "lat": datos.lat,
        "lng": datos.lng,
        "imagen": (datos.imagen or "").strip() or None,
        "credito": datos.credito.strip()[:255],
        "destacado": 1 if datos.destacado else 0,
        "orden": datos.orden,
        "activo": 1 if datos.activo else 0,
    }
    try:
        if ficha_id is None:
            resultado = await sesion.execute(
                text(
                    """
                    INSERT INTO turismo_fichas
                      (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, direccion, lat, lng,
                       imagen, credito, destacado, orden, activo)
                    VALUES
                      (:tipo, :categoria_id, :nombre, :slug, :resumen, :cuerpo, :zona, :direccion, :lat, :lng,
                       :imagen, :credito, :destacado, :orden, :activo)
                    """
                ),
                campos,
            )
            await sesion.commit()
            return resultado.lastrowid
        campos["id"] = ficha_id
        await sesion.execute(
            text(
                """
                UPDATE turismo_fichas
                   SET tipo = :tipo, categoria_id = :categoria_id, nombre = :nombre, resumen = :resumen,
                       cuerpo = :cuerpo, zona = :zona, direccion = :direccion, lat = :lat, lng = :lng,
                       imagen = :imagen, credito = :credito, destacado = :destacado, orden = :orden, activo = :activo
                 WHERE id = :id
                """
            ),
            campos,
        )
        await sesion.commit()
        return ficha_id
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)


@router.get("/admin/turismo/eventos")
async def admin_eventos(_: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT e.*, c.nombre AS categoria
                  FROM turismo_eventos e
                  LEFT JOIN turismo_categorias c ON c.id = e.categoria_id
                 ORDER BY e.inicio DESC
                """
            )
        )
    ).mappings().all()
    return [_fila_evento(dict(fila)) for fila in filas]


@router.post("/admin/turismo/eventos", status_code=201)
async def crear_evento(
    datos: TurismoEventoIn,
    _: dict = Depends(exigir_turismo),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    slug = await _slug_unico(sesion, "turismo_eventos", "slug", slugificar(datos.titulo), None)
    resultado = await _guardar_evento(sesion, datos, slug, None)
    return {"id": resultado, "slug": slug}


@router.patch("/admin/turismo/eventos/{evento_id}")
async def editar_evento(
    evento_id: int,
    datos: TurismoEventoIn,
    _: dict = Depends(exigir_turismo),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    actual = (await sesion.execute(text("SELECT slug FROM turismo_eventos WHERE id = :id"), {"id": evento_id})).first()
    if actual is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    await _guardar_evento(sesion, datos, actual[0], evento_id)
    return {"id": evento_id}


@router.delete("/admin/turismo/eventos/{evento_id}", status_code=204)
async def borrar_evento(
    evento_id: int,
    _: dict = Depends(exigir_turismo),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    resultado = await sesion.execute(text("DELETE FROM turismo_eventos WHERE id = :id"), {"id": evento_id})
    if resultado.rowcount == 0:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    await sesion.commit()


async def _guardar_evento(sesion: AsyncSession, datos: TurismoEventoIn, slug: str, evento_id: int | None) -> int:
    campos = {
        "categoria_id": datos.categoria_id,
        "titulo": datos.titulo.strip(),
        "slug": slug,
        "resumen": datos.resumen.strip(),
        "cuerpo": datos.cuerpo.strip(),
        "inicio": datos.inicio,
        "fin": datos.fin,
        "lugar": datos.lugar.strip()[:160],
        "imagen": (datos.imagen or "").strip() or None,
        "credito": datos.credito.strip()[:255],
        "activo": 1 if datos.activo else 0,
    }
    try:
        if evento_id is None:
            resultado = await sesion.execute(
                text(
                    """
                    INSERT INTO turismo_eventos
                      (categoria_id, titulo, slug, resumen, cuerpo, inicio, fin, lugar, imagen, credito, activo)
                    VALUES
                      (:categoria_id, :titulo, :slug, :resumen, :cuerpo, :inicio, :fin, :lugar, :imagen, :credito, :activo)
                    """
                ),
                campos,
            )
            await sesion.commit()
            return resultado.lastrowid
        campos["id"] = evento_id
        await sesion.execute(
            text(
                """
                UPDATE turismo_eventos
                   SET categoria_id = :categoria_id, titulo = :titulo, resumen = :resumen, cuerpo = :cuerpo,
                       inicio = :inicio, fin = :fin, lugar = :lugar, imagen = :imagen, credito = :credito, activo = :activo
                 WHERE id = :id
                """
            ),
            campos,
        )
        await sesion.commit()
        return evento_id
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)


@router.get("/admin/turismo/galeria")
async def admin_galeria(_: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    return await galeria(sesion)


@router.post("/admin/turismo/galeria", status_code=201)
async def crear_foto(
    titulo: str,
    descripcion: str = "",
    credito: str = "",
    orden: int = 0,
    archivo: UploadFile = File(),
    _: dict = Depends(exigir_turismo),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    nombre = await _guardar_imagen(archivo)
    resultado = await sesion.execute(
        text(
            """
            INSERT INTO turismo_galeria (titulo, descripcion, archivo, credito, orden, activo)
            VALUES (:titulo, :descripcion, :archivo, :credito, :orden, 1)
            """
        ),
        {
            "titulo": titulo.strip()[:160],
            "descripcion": descripcion.strip()[:300],
            "archivo": nombre,
            "credito": credito.strip()[:255],
            "orden": orden,
        },
    )
    await sesion.commit()
    return {"id": resultado.lastrowid, "url": f"/medios/{nombre}"}


@router.delete("/admin/turismo/galeria/{foto_id}", status_code=204)
async def borrar_foto(
    foto_id: int,
    _: dict = Depends(exigir_turismo),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    resultado = await sesion.execute(text("DELETE FROM turismo_galeria WHERE id = :id"), {"id": foto_id})
    if resultado.rowcount == 0:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    await sesion.commit()


@router.get("/admin/turismo/mensajes")
async def mensajes(_: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(text("SELECT id, nombre, email, mensaje, creado_en FROM turismo_mensajes ORDER BY id DESC LIMIT 50"))
    ).mappings().all()
    salida = []
    for fila in filas:
        item = dict(fila)
        item["creado_en"] = item["creado_en"].isoformat(sep=" ", timespec="minutes") if item["creado_en"] else None
        salida.append(item)
    return salida


@router.post("/admin/turismo/medios", status_code=201)
async def subir_medio(
    archivo: UploadFile = File(),
    _: dict = Depends(exigir_turismo),
):
    nombre = await _guardar_imagen(archivo)
    return {"archivo": nombre, "url": f"/medios/{nombre}"}


async def _guardar_imagen(archivo: UploadFile) -> str:
    sufijo = Path(archivo.filename or "").suffix.lower()
    extension = EXTENSIONES.get(sufijo)
    if extension is None:
        raise HTTPException(status_code=422, detail="La imagen debe ser JPG, PNG o WebP")
    contenido = await archivo.read()
    if not contenido or len(contenido) > 5 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="La imagen debe pesar entre 1 byte y 5 MB")
    MEDIOS.mkdir(parents=True, exist_ok=True)
    nombre = f"{token_hex(8)}{extension}"
    (MEDIOS / nombre).write_bytes(contenido)
    return nombre
