"""KPIs del tablero único. Cada operador recibe solo su módulo."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencias import exigir_panel, obtener_sesion

router = APIRouter()


@router.get("/admin/resumen")
async def resumen(usuario: dict = Depends(exigir_panel), sesion: AsyncSession = Depends(obtener_sesion)):
    rol = usuario["rol"]
    datos: dict = {"rol": rol, "modulos": _modulos(rol)}
    if rol in ("administrador", "operador_transporte"):
        ventas = (
            await sesion.execute(
                text(
                    """
                    SELECT COALESCE(SUM(monto), 0)
                      FROM pagos
                     WHERE estado = 'aprobado' AND DATE(pagado_en) = CURDATE()
                    """
                )
            )
        ).scalar_one()
        viajes = (
            await sesion.execute(
                text(
                    """
                    SELECT COUNT(*) FROM viajes
                     WHERE DATE(salida) = CURDATE() AND estado <> 'cancelado'
                    """
                )
            )
        ).scalar_one()
        ocupados = (
            await sesion.execute(
                text(
                    """
                    SELECT COUNT(*)
                      FROM boletos b
                      JOIN viajes v ON v.id = b.viaje_id
                     WHERE DATE(v.salida) = CURDATE()
                       AND v.estado <> 'cancelado'
                       AND b.estado IN ('pagado', 'reservado', 'usado')
                    """
                )
            )
        ).scalar_one()
        puestos = (
            await sesion.execute(
                text(
                    """
                    SELECT COUNT(*)
                      FROM viajes v
                      JOIN asientos a ON a.bus_id = v.bus_id
                     WHERE DATE(v.salida) = CURDATE() AND v.estado <> 'cancelado'
                    """
                )
            )
        ).scalar_one()
        datos["transporte"] = {
            "ventas_hoy": float(ventas),
            "viajes_hoy": int(viajes),
            "asientos_ocupados": int(ocupados),
            "asientos_totales": int(puestos),
            "ocupacion": round(int(ocupados) / int(puestos), 3) if puestos else 0,
        }
    if rol in ("administrador", "operador_turismo"):
        fichas = (await sesion.execute(text("SELECT COUNT(*) FROM turismo_fichas WHERE activo = 1"))).scalar_one()
        mensajes = (await sesion.execute(text("SELECT COUNT(*) FROM turismo_mensajes"))).scalar_one()
        eventos = (
            await sesion.execute(text("SELECT COUNT(*) FROM turismo_eventos WHERE activo = 1 AND inicio >= CURDATE()"))
        ).scalar_one()
        datos["turismo"] = {
            "fichas": int(fichas),
            "mensajes": int(mensajes),
            "eventos_proximos": int(eventos),
        }
    if rol in ("administrador", "operador_taxi"):
        viajes_taxi = (
            await sesion.execute(text("SELECT COUNT(*) FROM taxi_viajes WHERE DATE(creado_en) = CURDATE()"))
        ).scalar_one()
        datos["taxi"] = {"viajes_hoy": int(viajes_taxi)}
    return datos


def _modulos(rol: str) -> list[str]:
    if rol == "administrador":
        return ["resumen", "turismo", "transporte", "taxi"]
    return {
        "operador_turismo": ["turismo"],
        "operador_transporte": ["transporte"],
        "operador_taxi": ["taxi"],
    }.get(rol, [])
