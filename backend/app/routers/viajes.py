from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencias import obtener_sesion
from app.presentacion import fila_a_dict

router = APIRouter()


@router.get("")
async def buscar_viajes(
    origen: int = Query(gt=0),
    destino: int = Query(gt=0),
    fecha: date = Query(),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    if origen == destino:
        raise HTTPException(status_code=422, detail="El origen y el destino deben ser distintos")
    filas = (
        await sesion.execute(
            text(
                """
                SELECT v.id,
                       v.salida,
                       v.llegada_est,
                       v.precio,
                       v.estado,
                       co.nombre AS origen,
                       cd.nombre AS destino,
                       bu.placa,
                       bu.numero_disco,
                       bu.capacidad,
                       bu.pisos,
                       (
                         SELECT COUNT(*)
                           FROM v_disponibilidad d
                          WHERE d.viaje_id = v.id
                            AND d.estado_asiento = 'libre'
                       ) AS asientos_libres
                  FROM viajes v
                  JOIN rutas r ON r.id = v.ruta_id
                  JOIN ciudades co ON co.id = r.origen_id
                  JOIN ciudades cd ON cd.id = r.destino_id
                  JOIN buses bu ON bu.id = v.bus_id
                 WHERE r.origen_id = :origen
                   AND r.destino_id = :destino
                   AND v.salida >= :desde
                   AND v.salida < DATE_ADD(:desde, INTERVAL 1 DAY)
                   AND v.salida > NOW()
                   AND v.estado = 'programado'
                 ORDER BY v.salida
                """
            ),
            {"origen": origen, "destino": destino, "desde": fecha},
        )
    ).mappings().all()
    return [fila_a_dict(fila) for fila in filas]


@router.get("/proximas")
async def proximas_fechas(
    origen: int = Query(gt=0),
    destino: int = Query(gt=0),
    desde: date | None = Query(default=None),
    limite: int = Query(default=4, ge=1, le=8),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    if origen == destino:
        raise HTTPException(status_code=422, detail="El origen y el destino deben ser distintos")
    filas = (
        await sesion.execute(
            text(
                """
                SELECT fecha, salidas
                  FROM (
                        SELECT DATE(v.salida) AS fecha, COUNT(*) AS salidas
                          FROM viajes v
                          JOIN rutas r ON r.id = v.ruta_id
                         WHERE r.origen_id = :origen
                           AND r.destino_id = :destino
                           AND v.estado = 'programado'
                           AND v.salida > NOW()
                           AND DATE(v.salida) <> COALESCE(:desde, CURDATE())
                         GROUP BY DATE(v.salida)
                       ) fechas
                 ORDER BY (fecha > COALESCE(:desde, CURDATE())) DESC, fecha
                 LIMIT :limite
                """
            ),
            {"origen": origen, "destino": destino, "desde": desde, "limite": limite},
        )
    ).mappings().all()
    return [fila_a_dict(fila) for fila in filas]


@router.get("/{viaje_id}/asientos")
async def asientos_del_viaje(viaje_id: int, sesion: AsyncSession = Depends(obtener_sesion)):
    viaje = (
        await sesion.execute(
            text(
                """
                SELECT v.id,
                       v.salida,
                       v.llegada_est,
                       v.precio,
                       v.estado,
                       co.nombre AS origen,
                       cd.nombre AS destino,
                       bu.placa,
                       bu.numero_disco,
                       bu.capacidad,
                       bu.pisos
                  FROM viajes v
                  JOIN rutas r ON r.id = v.ruta_id
                  JOIN ciudades co ON co.id = r.origen_id
                  JOIN ciudades cd ON cd.id = r.destino_id
                  JOIN buses bu ON bu.id = v.bus_id
                 WHERE v.id = :viaje_id
                """
            ),
            {"viaje_id": viaje_id},
        )
    ).mappings().first()
    if viaje is None:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    asientos = (
        await sesion.execute(
            text(
                """
                SELECT asiento_id, numero, piso, fila, columna, tipo, estado_asiento
                  FROM v_disponibilidad
                 WHERE viaje_id = :viaje_id
                 ORDER BY piso, fila, columna
                """
            ),
            {"viaje_id": viaje_id},
        )
    ).mappings().all()
    return {
        "viaje": fila_a_dict(viaje),
        "asientos": [
            {
                "id": fila["asiento_id"],
                "numero": fila["numero"],
                "piso": fila["piso"],
                "fila": fila["fila"],
                "columna": fila["columna"],
                "tipo": fila["tipo"],
                "estado": fila["estado_asiento"],
            }
            for fila in asientos
        ],
    }
