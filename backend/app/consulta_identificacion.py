"""Consulta de razón social: primero la tabla local, luego un proveedor HTTP opcional.

El proveedor externo es un servicio de pago contratado. Esta capa solo acepta JSON.
No descarga ni interpreta páginas del SRI ni del Registro Civil.
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

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
        return {
            "encontrado": True,
            "origen": "local",
            "tipo": fila["tipo"],
            "identificacion": fila["identificacion"],
            "razon_social": fila["razon_social"],
            "direccion": fila["direccion"] or "",
            "email": fila["email"] or "",
            "telefono": fila["telefono"] or "",
        }
    externo = await _consultar_externo(tipo, identificacion)
    if externo is not None:
        return externo
    return {"encontrado": False, "origen": None, "identificacion": identificacion, "tipo": tipo}


async def _consultar_externo(tipo: str, identificacion: str) -> dict | None:
    url = settings.identificacion_lookup_url.strip()
    if not url or tipo not in ("cedula", "ruc"):
        return None
    import httpx

    headers = {"Accept": "application/json"}
    if settings.identificacion_lookup_api_key.strip():
        headers["Authorization"] = f"Bearer {settings.identificacion_lookup_api_key.strip()}"
    try:
        async with httpx.AsyncClient(timeout=5, follow_redirects=False) as cliente:
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
    razon = str(datos.get("razon_social") or datos.get("nombre") or "").strip()
    if not razon:
        return None
    return {
        "encontrado": True,
        "origen": "externo",
        "tipo": tipo,
        "identificacion": identificacion,
        "razon_social": razon[:300],
        "direccion": str(datos.get("direccion") or "").strip()[:300],
        "email": str(datos.get("email") or "").strip()[:180],
        "telefono": str(datos.get("telefono") or "").strip()[:30],
    }
