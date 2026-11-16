"""Portal Aprende: cursos, lecciones, artículos e inscripciones."""

import logging
import smtplib
from email.message import EmailMessage

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencias import exigir_pasajero, exigir_turismo, obtener_sesion
from app.identificacion import cedula_valida
from app.slug import slugificar

router = APIRouter()
log = logging.getLogger("lamana.cursos")


def _aviso_correo(destino: str, curso: str) -> None:
    if not settings.smtp_host.strip():
        log.info("Inscripción sin SMTP para %s en %s", destino, curso)
        return
    mensaje = EmailMessage()
    mensaje["Subject"] = f"Inscripción recibida · {curso}"
    mensaje["From"] = settings.smtp_desde
    mensaje["To"] = destino
    mensaje.set_content(
        f"Recibimos tu inscripción a «{curso}» en La Maná Recorres.\n"
        "Si el curso es de ejemplo, no es una oferta oficial.\n"
    )
    with smtplib.SMTP(settings.smtp_host.strip(), settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_port != 25:
            smtp.starttls()
        if settings.smtp_usuario.strip():
            smtp.login(settings.smtp_usuario.strip(), settings.smtp_clave)
        smtp.send_message(mensaje)


def _curso(fila, ocupados: int = 0) -> dict:
    return {
        "id": int(fila["id"]),
        "titulo": fila["titulo"],
        "slug": fila["slug"],
        "resumen": fila["resumen"],
        "descripcion": fila.get("descripcion") or "",
        "objetivos": fila.get("objetivos") or "",
        "requisitos": fila.get("requisitos") or "",
        "nivel": fila["nivel"],
        "duracion_horas": int(fila["duracion_horas"]),
        "modalidad": fila["modalidad"],
        "gratis": bool(fila["gratis"]),
        "costo": None if fila.get("costo") is None else float(fila["costo"]),
        "cupos": int(fila["cupos"]),
        "ocupados": ocupados,
        "imagen": fila.get("imagen"),
        "lugar": fila.get("lugar") or "",
        "enlace": fila.get("enlace") or "",
        "inicio": fila["inicio"].isoformat() if fila.get("inicio") else None,
        "fin": fila["fin"].isoformat() if fila.get("fin") else None,
        "certificado": bool(fila["certificado"]),
        "destacado": bool(fila["destacado"]),
        "activo": bool(fila["activo"]),
        "ejemplo": bool(fila["ejemplo"]),
        "categoria": fila.get("categoria"),
        "categoria_slug": fila.get("categoria_slug"),
        "instructor": fila.get("instructor"),
        "institucion": fila.get("institucion") or "",
    }


_SQL_CURSO = """
    SELECT c.*, cat.nombre AS categoria, cat.slug AS categoria_slug,
           i.nombre AS instructor, i.institucion
      FROM cursos c
      LEFT JOIN cursos_categorias cat ON cat.id = c.categoria_id
      LEFT JOIN cursos_instructores i ON i.id = c.instructor_id
"""


async def _ocupados(sesion, curso_id: int) -> int:
    return int(
        (
            await sesion.execute(
                text("SELECT COUNT(*) FROM curso_inscripciones WHERE curso_id = :id AND estado <> 'cancelado'"),
                {"id": curso_id},
            )
        ).scalar_one()
    )


@router.get("/aprende/resumen")
async def resumen(sesion: AsyncSession = Depends(obtener_sesion)):
    categorias = (
        await sesion.execute(text("SELECT id, nombre, slug FROM cursos_categorias WHERE activo = 1 ORDER BY orden, nombre"))
    ).mappings().all()
    destacados = (
        await sesion.execute(text(_SQL_CURSO + " WHERE c.activo = 1 AND c.destacado = 1 ORDER BY c.inicio LIMIT 6"))
    ).mappings().all()
    proximos = (
        await sesion.execute(
            text(_SQL_CURSO + " WHERE c.activo = 1 AND c.inicio IS NOT NULL AND c.inicio >= CURDATE() ORDER BY c.inicio LIMIT 6")
        )
    ).mappings().all()
    articulos = (
        await sesion.execute(
            text(
                """
                SELECT id, titulo, slug, resumen, categoria, destacado, ejemplo
                  FROM cursos_articulos WHERE activo = 1
                 ORDER BY destacado DESC, id DESC LIMIT 6
                """
            )
        )
    ).mappings().all()
    return {
        "categorias": [dict(fila) for fila in categorias],
        "destacados": [_curso(fila) for fila in destacados],
        "proximos": [_curso(fila) for fila in proximos],
        "articulos": [dict(fila) for fila in articulos],
    }


@router.get("/aprende/cursos")
async def listar(categoria: str = "", q: str = "", sesion: AsyncSession = Depends(obtener_sesion)):
    sql = _SQL_CURSO + " WHERE c.activo = 1"
    params: dict = {}
    if categoria:
        sql += " AND cat.slug = :categoria"
        params["categoria"] = categoria
    if q.strip():
        sql += " AND (c.titulo LIKE :q OR c.resumen LIKE :q)"
        params["q"] = f"%{q.strip()}%"
    sql += " ORDER BY c.destacado DESC, c.inicio, c.titulo"
    filas = (await sesion.execute(text(sql), params)).mappings().all()
    salida = []
    for fila in filas:
        salida.append(_curso(fila, await _ocupados(sesion, int(fila["id"]))))
    return salida


@router.get("/aprende/cursos/{slug}")
async def detalle(slug: str, sesion: AsyncSession = Depends(obtener_sesion)):
    fila = (await sesion.execute(text(_SQL_CURSO + " WHERE c.slug = :slug AND c.activo = 1"), {"slug": slug})).mappings().first()
    if fila is None:
        raise HTTPException(status_code=404, detail="No encontramos ese curso")
    modulos = (
        await sesion.execute(text("SELECT id, titulo, orden FROM curso_modulos WHERE curso_id = :id ORDER BY orden, id"), {"id": fila["id"]})
    ).mappings().all()
    lecciones = (
        await sesion.execute(
            text(
                """
                SELECT l.id, l.modulo_id, l.titulo, l.orden, l.tipo, l.cuerpo, l.video_url, l.pdf_url
                  FROM curso_lecciones l
                  JOIN curso_modulos m ON m.id = l.modulo_id
                 WHERE m.curso_id = :id
                 ORDER BY l.orden, l.id
                """
            ),
            {"id": fila["id"]},
        )
    ).mappings().all()
    cuerpo = _curso(fila, await _ocupados(sesion, int(fila["id"])))
    cuerpo["modulos"] = []
    for modulo in modulos:
        cuerpo["modulos"].append({
            "id": int(modulo["id"]),
            "titulo": modulo["titulo"],
            "lecciones": [
                {
                    "id": int(item["id"]),
                    "titulo": item["titulo"],
                    "tipo": item["tipo"],
                    "cuerpo": item["cuerpo"],
                    "video_url": item["video_url"],
                    "pdf_url": item["pdf_url"],
                }
                for item in lecciones if int(item["modulo_id"]) == int(modulo["id"])
            ],
        })
    return cuerpo


@router.post("/aprende/cursos/{slug}/inscripcion", status_code=201)
async def inscribir(slug: str, cuerpo: dict, sesion: AsyncSession = Depends(obtener_sesion)):
    fila = (await sesion.execute(text("SELECT id, titulo, cupos, activo FROM cursos WHERE slug = :slug"), {"slug": slug})).mappings().first()
    if fila is None or not fila["activo"]:
        raise HTTPException(status_code=404, detail="Ese curso no está publicado")
    nombre = str(cuerpo.get("nombre") or "").strip()
    documento = "".join(ch for ch in str(cuerpo.get("documento") or "") if ch.isdigit())
    email = str(cuerpo.get("email") or "").strip().lower()
    telefono = str(cuerpo.get("telefono") or "").strip()[:30]
    if len(nombre) < 3:
        raise HTTPException(status_code=422, detail="Escribe tu nombre completo")
    if not cedula_valida(documento):
        raise HTTPException(status_code=422, detail="La cédula no es válida")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=422, detail="Escribe un correo válido")
    if await _ocupados(sesion, int(fila["id"])) >= int(fila["cupos"]):
        raise HTTPException(status_code=409, detail="Ya no quedan cupos en este curso")
    try:
        await sesion.execute(
            text(
                """
                INSERT INTO curso_inscripciones (curso_id, nombre, documento, email, telefono, estado)
                VALUES (:curso, :nombre, :documento, :email, :telefono, 'inscrito')
                """
            ),
            {"curso": fila["id"], "nombre": nombre, "documento": documento, "email": email, "telefono": telefono},
        )
        await sesion.commit()
    except IntegrityError:
        await sesion.rollback()
        raise HTTPException(status_code=409, detail="Esa cédula ya está inscrita en este curso")
    _aviso_correo(email, fila["titulo"])
    return {"estado": "inscrito", "curso": fila["titulo"], "cupos_restantes": int(fila["cupos"]) - await _ocupados(sesion, int(fila["id"]))}


@router.get("/aprende/articulos")
async def articulos(sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(text("SELECT id, titulo, slug, resumen, categoria, destacado, ejemplo FROM cursos_articulos WHERE activo = 1 ORDER BY destacado DESC, id DESC"))
    ).mappings().all()
    return [dict(fila) for fila in filas]


@router.get("/aprende/articulos/{slug}")
async def articulo(slug: str, sesion: AsyncSession = Depends(obtener_sesion)):
    fila = (await sesion.execute(text("SELECT * FROM cursos_articulos WHERE slug = :slug AND activo = 1"), {"slug": slug})).mappings().first()
    if fila is None:
        raise HTTPException(status_code=404, detail="No encontramos ese artículo")
    return dict(fila)


@router.get("/aprende/progreso/{slug}")
async def progreso(slug: str, usuario: dict = Depends(exigir_pasajero), sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT p.leccion_id
                  FROM curso_progreso p
                  JOIN curso_lecciones l ON l.id = p.leccion_id
                  JOIN curso_modulos m ON m.id = l.modulo_id
                  JOIN cursos c ON c.id = m.curso_id
                 WHERE p.usuario_id = :usuario AND c.slug = :slug
                """
            ),
            {"usuario": usuario["id"], "slug": slug},
        )
    ).all()
    return {"lecciones": [int(fila[0]) for fila in filas]}


@router.post("/aprende/lecciones/{leccion_id}/completar")
async def completar(leccion_id: int, usuario: dict = Depends(exigir_pasajero), sesion: AsyncSession = Depends(obtener_sesion)):
    existe = (await sesion.execute(text("SELECT id FROM curso_lecciones WHERE id = :id"), {"id": leccion_id})).first()
    if existe is None:
        raise HTTPException(status_code=404, detail="No encontramos esa lección")
    await sesion.execute(
        text(
            """
            INSERT IGNORE INTO curso_progreso (usuario_id, leccion_id)
            VALUES (:usuario, :leccion)
            """
        ),
        {"usuario": usuario["id"], "leccion": leccion_id},
    )
    await sesion.commit()
    return {"completada": True}


@router.get("/admin/cursos/catalogo")
async def catalogo(_: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    categorias = (await sesion.execute(text("SELECT * FROM cursos_categorias ORDER BY orden, nombre"))).mappings().all()
    instructores = (await sesion.execute(text("SELECT * FROM cursos_instructores ORDER BY nombre"))).mappings().all()
    cursos = (await sesion.execute(text(_SQL_CURSO + " ORDER BY c.id DESC"))).mappings().all()
    articulos = (await sesion.execute(text("SELECT * FROM cursos_articulos ORDER BY id DESC"))).mappings().all()
    return {
        "categorias": [dict(fila) for fila in categorias],
        "instructores": [dict(fila) for fila in instructores],
        "cursos": [_curso(fila, await _ocupados(sesion, int(fila["id"]))) for fila in cursos],
        "articulos": [dict(fila) for fila in articulos],
    }


@router.post("/admin/cursos/categorias", status_code=201)
async def crear_categoria(cuerpo: dict, _: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    nombre = str(cuerpo.get("nombre") or "").strip()
    if len(nombre) < 3:
        raise HTTPException(status_code=422, detail="Ponle un nombre a la categoría")
    slug = slugificar(nombre)
    await sesion.execute(
        text("INSERT INTO cursos_categorias (nombre, slug, orden) VALUES (:nombre, :slug, :orden)"),
        {"nombre": nombre, "slug": slug, "orden": int(cuerpo.get("orden") or 0)},
    )
    await sesion.commit()
    return {"slug": slug}


@router.post("/admin/cursos", status_code=201)
async def crear_curso(cuerpo: dict, _: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    titulo = str(cuerpo.get("titulo") or "").strip()
    if len(titulo) < 4:
        raise HTTPException(status_code=422, detail="El título del curso es muy corto")
    slug = slugificar(titulo)
    resultado = await sesion.execute(
        text(
            """
            INSERT INTO cursos (
              categoria_id, instructor_id, titulo, slug, resumen, descripcion, objetivos, requisitos,
              nivel, duracion_horas, modalidad, gratis, costo, cupos, lugar, enlace, inicio,
              certificado, destacado, activo, ejemplo
            ) VALUES (
              :categoria, :instructor, :titulo, :slug, :resumen, :descripcion, :objetivos, :requisitos,
              :nivel, :horas, :modalidad, :gratis, :costo, :cupos, :lugar, '', :inicio,
              :certificado, :destacado, :activo, 0
            )
            """
        ),
        {
            "categoria": cuerpo.get("categoria_id") or None,
            "instructor": cuerpo.get("instructor_id") or None,
            "titulo": titulo,
            "slug": slug,
            "resumen": str(cuerpo.get("resumen") or "")[:400],
            "descripcion": str(cuerpo.get("descripcion") or titulo),
            "objetivos": str(cuerpo.get("objetivos") or ""),
            "requisitos": str(cuerpo.get("requisitos") or "")[:400],
            "nivel": cuerpo.get("nivel") or "basico",
            "horas": int(cuerpo.get("duracion_horas") or 4),
            "modalidad": cuerpo.get("modalidad") or "presencial",
            "gratis": 1 if cuerpo.get("gratis", True) else 0,
            "costo": cuerpo.get("costo"),
            "cupos": int(cuerpo.get("cupos") or 20),
            "lugar": str(cuerpo.get("lugar") or "")[:180],
            "inicio": cuerpo.get("inicio") or None,
            "certificado": 1 if cuerpo.get("certificado") else 0,
            "destacado": 1 if cuerpo.get("destacado") else 0,
            "activo": 1 if cuerpo.get("activo", True) else 0,
        },
    )
    await sesion.commit()
    return {"id": resultado.lastrowid, "slug": slug}


@router.patch("/admin/cursos/{curso_id}")
async def editar_curso(curso_id: int, cuerpo: dict, _: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    if "activo" in cuerpo:
        await sesion.execute(
            text("UPDATE cursos SET activo = :activo WHERE id = :id"),
            {"activo": 1 if cuerpo["activo"] else 0, "id": curso_id},
        )
        await sesion.commit()
    return {"id": curso_id}


@router.delete("/admin/cursos/{curso_id}", status_code=204)
async def borrar_curso(curso_id: int, _: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    await sesion.execute(
        text(
            """
            DELETE l FROM curso_lecciones l
              JOIN curso_modulos m ON m.id = l.modulo_id
             WHERE m.curso_id = :id
            """
        ),
        {"id": curso_id},
    )
    await sesion.execute(text("DELETE FROM curso_modulos WHERE curso_id = :id"), {"id": curso_id})
    await sesion.execute(text("DELETE FROM curso_inscripciones WHERE curso_id = :id"), {"id": curso_id})
    await sesion.execute(text("DELETE FROM cursos WHERE id = :id"), {"id": curso_id})
    await sesion.commit()


@router.post("/admin/cursos/{curso_id}/modulos", status_code=201)
async def crear_modulo(curso_id: int, cuerpo: dict, _: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    titulo = str(cuerpo.get("titulo") or "").strip()
    if len(titulo) < 2:
        raise HTTPException(status_code=422, detail="El módulo necesita un título")
    resultado = await sesion.execute(
        text("INSERT INTO curso_modulos (curso_id, titulo, orden) VALUES (:curso, :titulo, :orden)"),
        {"curso": curso_id, "titulo": titulo, "orden": int(cuerpo.get("orden") or 1)},
    )
    await sesion.commit()
    return {"id": resultado.lastrowid}


@router.post("/admin/cursos/modulos/{modulo_id}/lecciones", status_code=201)
async def crear_leccion(modulo_id: int, cuerpo: dict, _: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    titulo = str(cuerpo.get("titulo") or "").strip()
    if len(titulo) < 2:
        raise HTTPException(status_code=422, detail="La lección necesita un título")
    tipo = cuerpo.get("tipo") or "texto"
    if tipo not in {"texto", "video", "pdf"}:
        raise HTTPException(status_code=422, detail="El tipo debe ser texto, video o pdf")
    resultado = await sesion.execute(
        text(
            """
            INSERT INTO curso_lecciones (modulo_id, titulo, orden, tipo, cuerpo, video_url, pdf_url)
            VALUES (:modulo, :titulo, :orden, :tipo, :cuerpo, :video, :pdf)
            """
        ),
        {
            "modulo": modulo_id,
            "titulo": titulo,
            "orden": int(cuerpo.get("orden") or 1),
            "tipo": tipo,
            "cuerpo": str(cuerpo.get("cuerpo") or ""),
            "video": str(cuerpo.get("video_url") or "")[:300],
            "pdf": str(cuerpo.get("pdf_url") or "")[:300],
        },
    )
    await sesion.commit()
    return {"id": resultado.lastrowid}


@router.post("/admin/cursos/articulos", status_code=201)
async def crear_articulo(cuerpo: dict, _: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    titulo = str(cuerpo.get("titulo") or "").strip()
    if len(titulo) < 4:
        raise HTTPException(status_code=422, detail="El artículo necesita un título")
    slug = slugificar(titulo)
    await sesion.execute(
        text(
            """
            INSERT INTO cursos_articulos (titulo, slug, resumen, cuerpo, categoria, destacado, activo, ejemplo)
            VALUES (:titulo, :slug, :resumen, :cuerpo, :categoria, :destacado, 1, 0)
            """
        ),
        {
            "titulo": titulo,
            "slug": slug,
            "resumen": str(cuerpo.get("resumen") or "")[:400],
            "cuerpo": str(cuerpo.get("cuerpo") or titulo),
            "categoria": str(cuerpo.get("categoria") or "ciudadania")[:80],
            "destacado": 1 if cuerpo.get("destacado") else 0,
        },
    )
    await sesion.commit()
    return {"slug": slug}


@router.get("/admin/cursos/{curso_id}/inscritos")
async def inscritos(curso_id: int, _: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text("SELECT id, nombre, documento, email, telefono, estado, creado_en FROM curso_inscripciones WHERE curso_id = :id ORDER BY id DESC"),
            {"id": curso_id},
        )
    ).mappings().all()
    return [
        {**dict(fila), "creado_en": fila["creado_en"].isoformat(sep=" ", timespec="minutes") if fila["creado_en"] else None}
        for fila in filas
    ]


@router.get("/admin/cursos/{curso_id}/inscritos.csv")
async def inscritos_csv(curso_id: int, _: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    filas = await inscritos(curso_id, _, sesion)
    lineas = ["nombre,documento,email,telefono,estado"]
    for fila in filas:
        lineas.append(",".join(str(fila[clave]).replace(",", " ") for clave in ("nombre", "documento", "email", "telefono", "estado")))
    return Response(
        content="\n".join(lineas),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="inscritos-{curso_id}.csv"'},
    )


@router.patch("/admin/cursos/inscripciones/{inscripcion_id}")
async def estado_inscripcion(inscripcion_id: int, cuerpo: dict, _: dict = Depends(exigir_turismo), sesion: AsyncSession = Depends(obtener_sesion)):
    estado = cuerpo.get("estado")
    if estado not in {"inscrito", "confirmado", "asistio", "certificado", "cancelado"}:
        raise HTTPException(status_code=422, detail="Estado no reconocido")
    await sesion.execute(
        text("UPDATE curso_inscripciones SET estado = :estado WHERE id = :id"),
        {"estado": estado, "id": inscripcion_id},
    )
    await sesion.commit()
    return {"id": inscripcion_id, "estado": estado}
