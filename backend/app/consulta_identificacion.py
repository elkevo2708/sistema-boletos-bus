"""Consulta de razón social: tabla local, luego un proveedor HTTP o el catálogo demo.

El proveedor externo es un servicio de pago contratado. Esta capa solo acepta JSON
y arma el nombre con el mapeo de campos configurado por entorno.
No descarga ni interpreta páginas del SRI ni del Registro Civil.
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.demo_cedulas import buscar_demo

log = logging.getLogger("lamana.consulta")

_SELECT = """
SELECT identificacion, tipo, razon_social, direccion, email, telefono
  FROM clientes_facturacion
 WHERE identificacion = :identificacion
"""


async def consultar_identificacion(sesion: AsyncSession, tipo: str, identificacion: str) -> dict:
    fila = (
        await sesion.execute(text(_SELECT), {"identificacion": identificacion})
    ).mappings().first()
    if fila is not None:
        return _respuesta(True, "local", fila["tipo"], fila["identificacion"], fila["razon_social"], fila["direccion"], fila["email"], fila["telefono"])
    externo = await _consultar_externo(tipo, identificacion)
    if externo is not None:
        return externo
    if not settings.identificacion_lookup_url.strip():
        demo = buscar_demo(identificacion)
        if demo is not None and demo["tipo"] == tipo:
            return _respuesta(True, "demo", tipo, identificacion, demo["razon_social"], demo["direccion"], demo["email"], demo["telefono"])
    return {"encontrado": False, "origen": None, "identificacion": identificacion, "tipo": tipo}


def extraer(datos: dict, ruta: str) -> str:
    actual: object = datos
    for parte in ruta.split("."):
        if not isinstance(actual, dict) or parte not in actual:
            return ""
        actual = actual[parte]
    if actual is None:
        return ""
    return str(actual).strip()


def armar_nombre(datos: dict) -> str:
    campos = [parte.strip() for parte in settings.identificacion_lookup_campo_nombre.split(",") if parte.strip()]
    partes = [extraer(datos, campo) for campo in campos]
    partes = [parte for parte in partes if parte]
    if partes:
        return " ".join(partes)[:300]
    for reserva in ("razon_social", "nombre", "nombreCompleto", "data.nombreCompleto", "data.nombres"):
        valor = extraer(datos, reserva)
        if valor:
            return valor[:300]
    return ""


async def _consultar_externo(tipo: str, identificacion: str) -> dict | None:
    url = settings.identificacion_lookup_url.strip()
    if not url or tipo not in ("cedula", "ruc"):
        return None
    import httpx

    headers = {"Accept": "application/json"}
    clave = settings.identificacion_lookup_api_key.strip()
    if clave:
        nombre = settings.identificacion_lookup_header.strip() or "Authorization"
        esquema = settings.identificacion_lookup_scheme.strip()
        headers[nombre] = f"{esquema} {clave}".strip() if esquema else clave
    try:
        async with httpx.AsyncClient(timeout=5, follow_redirects=False) as cliente:
            if settings.identificacion_lookup_metodo.strip().upper() == "POST":
                respuesta = await cliente.post(url, json={"tipo": tipo, "identificacion": identificacion}, headers=headers)
            else:
                respuesta = await cliente.get(
                    url,
                    params={"tipo": tipo, "identificacion": identificacion},
                    headers=headers,
                )
        if respuesta.status_code != 200:
            log.info("Consulta externa de identificación respondió %s", respuesta.status_code)
            return None
        if "json" not in respuesta.headers.get("content-type", "").lower():
            log.info("La consulta externa no devolvió JSON; se ignora")
            return None
        datos = respuesta.json()
    except Exception as exc:
        log.warning("No se pudo consultar el proveedor de identificación: %s", exc)
        return None
    if not isinstance(datos, dict):
        return None
    razon = armar_nombre(datos)
    if not razon:
        return None
    return _respuesta(
        True,
        "externo",
        tipo,
        identificacion,
        razon,
        extraer(datos, settings.identificacion_lookup_campo_direccion.strip() or "direccion"),
        extraer(datos, settings.identificacion_lookup_campo_email.strip() or "email"),
        extraer(datos, settings.identificacion_lookup_campo_telefono.strip() or "telefono"),
    )


def _respuesta(encontrado: bool, origen: str, tipo: str, identificacion: str, razon: str, direccion, email, telefono) -> dict:
    return {
        "encontrado": encontrado,
        "origen": origen,
        "tipo": tipo,
        "identificacion": identificacion,
        "razon_social": str(razon or "").strip()[:300],
        "direccion": str(direccion or "").strip()[:300],
        "email": str(email or "").strip()[:180],
        "telefono": str(telefono or "").strip()[:30],
    }
