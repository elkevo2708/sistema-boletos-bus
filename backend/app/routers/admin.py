from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencias import exigir_admin, obtener_sesion
from app.errores import traducir_error_mysql
from app.esquemas import TarifaIn, ViajeIn
from app.presentacion import fila_a_dict, limpiar
from app.tiempo import ahora_colombia

router = APIRouter()


@router.get("/rutas")
async def listar_rutas(
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT r.id, r.duracion_min, r.precio_base, r.activa,
                       co.nombre AS origen, cd.nombre AS destino
                  FROM rutas r
                  JOIN ciudades co ON co.id = r.origen_id
                  JOIN ciudades cd ON cd.id = r.destino_id
                 ORDER BY co.nombre, cd.nombre
                """
            )
        )
    ).mappings().all()
    return [fila_a_dict(fila) for fila in filas]


@router.get("/buses")
async def listar_buses(
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT id, placa, numero_disco, capacidad, pisos, estado
                  FROM buses
                 ORDER BY numero_disco
                """
            )
        )
    ).mappings().all()
    return [dict(fila) for fila in filas]


@router.post("/viajes", status_code=201)
async def crear_viaje(
    datos: ViajeIn,
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    if datos.salida <= ahora_colombia():
        raise HTTPException(status_code=422, detail="La salida debe ser futura")
    ruta = (
        await sesion.execute(
            text(
                """
                SELECT id, duracion_min, precio_base
                  FROM rutas
                 WHERE id = :id AND activa = 1
                """
            ),
            {"id": datos.ruta_id},
        )
    ).mappings().first()
    if ruta is None:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    precio: Decimal = datos.precio if datos.precio is not None else Decimal(ruta["precio_base"])
    llegada = datos.salida + timedelta(minutes=int(ruta["duracion_min"]))
    try:
        resultado = await sesion.execute(
            text(
                """
                INSERT INTO viajes (ruta_id, bus_id, salida, llegada_est, precio, estado)
                VALUES (:ruta_id, :bus_id, :salida, :llegada, :precio, 'programado')
                """
            ),
            {
                "ruta_id": datos.ruta_id,
                "bus_id": datos.bus_id,
                "salida": datos.salida.replace(tzinfo=None),
                "llegada": llegada.replace(tzinfo=None),
                "precio": precio,
            },
        )
        await sesion.commit()
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)
    viaje_id = resultado.lastrowid
    fila = (
        await sesion.execute(
            text(
                """
                SELECT id, ruta_id, bus_id, salida, llegada_est, precio, estado
                  FROM viajes
                 WHERE id = :id
                """
            ),
            {"id": viaje_id},
        )
    ).mappings().one()
    return fila_a_dict(fila)


@router.patch("/rutas/{ruta_id}/tarifa")
async def cambiar_tarifa(
    ruta_id: int,
    datos: TarifaIn,
    usuario: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    try:
        ruta = (
            await sesion.execute(
                text("SELECT id, precio_base FROM rutas WHERE id = :id FOR UPDATE"),
                {"id": ruta_id},
            )
        ).mappings().first()
        if ruta is None:
            raise HTTPException(status_code=404, detail="Ruta no encontrada")
        anterior = ruta["precio_base"]
        await sesion.execute(
            text("UPDATE rutas SET precio_base = :precio WHERE id = :id"),
            {"precio": datos.precio_base, "id": ruta_id},
        )
        await sesion.execute(
            text(
                """
                INSERT INTO auditoria (usuario_id, accion, entidad, entidad_id, detalle)
                VALUES (
                  :usuario_id,
                  'actualizar_tarifa',
                  'rutas',
                  :entidad_id,
                  JSON_OBJECT('precio_anterior', :anterior, 'precio_nuevo', :nuevo)
                )
                """
            ),
            {
                "usuario_id": usuario["id"],
                "entidad_id": str(ruta_id),
                "anterior": str(anterior),
                "nuevo": str(datos.precio_base),
            },
        )
        await sesion.commit()
    except HTTPException:
        await sesion.rollback()
        raise
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)
    return {
        "id": ruta_id,
        "precio_base": f"{datos.precio_base:.2f}",
        "precio_anterior": limpiar(anterior),
    }


@router.get("/ventas")
async def ventas_del_dia(
    fecha: date | None = Query(default=None),
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    if fecha is None:
        filas = (
            await sesion.execute(
                text(
                    """
                    SELECT fecha, ruta_id, origen, destino, boletos_pagados, total
                      FROM v_ventas_dia
                     WHERE fecha = CURDATE()
                     ORDER BY origen, destino
                    """
                )
            )
        ).mappings().all()
        fecha_txt = (
            await sesion.execute(text("SELECT CURDATE() AS fecha"))
        ).scalar_one()
        fecha_iso = limpiar(fecha_txt)
    else:
        filas = (
            await sesion.execute(
                text(
                    """
                    SELECT fecha, ruta_id, origen, destino, boletos_pagados, total
                      FROM v_ventas_dia
                     WHERE fecha = :fecha
                     ORDER BY origen, destino
                    """
                ),
                {"fecha": fecha},
            )
        ).mappings().all()
        fecha_iso = fecha.isoformat()
    registros = [fila_a_dict(fila) for fila in filas]
    total = sum(Decimal(fila["total"]) for fila in registros)
    return {
        "fecha": fecha_iso,
        "filas": registros,
        "total": f"{total:.2f}",
    }
