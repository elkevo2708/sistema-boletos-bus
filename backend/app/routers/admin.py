from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencias import exigir_admin, obtener_sesion
from app.horarios import generar_salidas
from app.errores import traducir_error_mysql
from app.esquemas import BusEstadoIn, BusIn, CiudadIn, RutaIn, TarifaIn, ViajeIn
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


@router.get("/ciudades")
async def listar_ciudades_admin(
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    filas = (
        await sesion.execute(
            text("SELECT id, nombre, departamento FROM ciudades ORDER BY nombre, departamento")
        )
    ).mappings().all()
    return [dict(fila) for fila in filas]


@router.post("/ciudades", status_code=201)
async def crear_ciudad(
    datos: CiudadIn,
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    try:
        resultado = await sesion.execute(
            text("INSERT INTO ciudades (nombre, departamento) VALUES (:nombre, :departamento)"),
            {"nombre": datos.nombre, "departamento": datos.departamento},
        )
        await sesion.commit()
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)
    return {"id": resultado.lastrowid, "nombre": datos.nombre, "departamento": datos.departamento}


@router.delete("/ciudades/{ciudad_id}", status_code=204)
async def borrar_ciudad(
    ciudad_id: int,
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    try:
        resultado = await sesion.execute(text("DELETE FROM ciudades WHERE id = :id"), {"id": ciudad_id})
        if resultado.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ciudad no encontrada")
        await sesion.commit()
    except HTTPException:
        await sesion.rollback()
        raise
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)


@router.post("/rutas", status_code=201)
async def crear_ruta(
    datos: RutaIn,
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    try:
        resultado = await sesion.execute(
            text(
                """
                INSERT INTO rutas (origen_id, destino_id, duracion_min, precio_base, activa)
                VALUES (:origen, :destino, :duracion, :precio, 1)
                """
            ),
            {
                "origen": datos.origen_id,
                "destino": datos.destino_id,
                "duracion": datos.duracion_min,
                "precio": f"{datos.precio_base:.2f}",
            },
        )
        await sesion.commit()
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)
    return {
        "id": resultado.lastrowid,
        "origen_id": datos.origen_id,
        "destino_id": datos.destino_id,
        "duracion_min": datos.duracion_min,
        "precio_base": f"{datos.precio_base:.2f}",
        "activa": 1,
    }


@router.delete("/rutas/{ruta_id}", status_code=204)
async def borrar_ruta(
    ruta_id: int,
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    try:
        resultado = await sesion.execute(text("DELETE FROM rutas WHERE id = :id"), {"id": ruta_id})
        if resultado.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ruta no encontrada")
        await sesion.commit()
    except HTTPException:
        await sesion.rollback()
        raise
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)


@router.get("/buses")
async def listar_buses(
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT b.id, b.placa, b.numero_disco, b.capacidad, b.pisos, b.estado,
                       (SELECT COUNT(*) FROM asientos a WHERE a.bus_id = b.id) AS asientos
                  FROM buses b
                 ORDER BY b.numero_disco
                """
            )
        )
    ).mappings().all()
    return [dict(fila) for fila in filas]


def _asientos_de(bus_id: int, pisos: int, filas: int) -> list[dict]:
    puestos = []
    numero = 0
    for piso in range(1, pisos + 1):
        for fila in range(1, filas + 1):
            for columna in range(1, 5):
                numero += 1
                puestos.append(
                    {
                        "bus_id": bus_id,
                        "numero": numero,
                        "piso": piso,
                        "fila": fila,
                        "columna": columna,
                        "tipo": "ventana" if columna in (1, 4) else "pasillo",
                    }
                )
    return puestos


@router.post("/buses", status_code=201)
async def crear_bus(
    datos: BusIn,
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    capacidad = datos.pisos * datos.filas * 4
    try:
        resultado = await sesion.execute(
            text(
                """
                INSERT INTO buses (placa, numero_disco, capacidad, pisos, estado)
                VALUES (:placa, :disco, :capacidad, :pisos, :estado)
                """
            ),
            {
                "placa": datos.placa,
                "disco": datos.numero_disco,
                "capacidad": capacidad,
                "pisos": datos.pisos,
                "estado": datos.estado,
            },
        )
        bus_id = int(resultado.lastrowid)
        for puesto in _asientos_de(bus_id, datos.pisos, datos.filas):
            await sesion.execute(
                text(
                    """
                    INSERT INTO asientos (bus_id, numero, piso, fila, columna, tipo)
                    VALUES (:bus_id, :numero, :piso, :fila, :columna, :tipo)
                    """
                ),
                puesto,
            )
        await sesion.commit()
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)
    return {
        "id": bus_id,
        "placa": datos.placa,
        "numero_disco": datos.numero_disco,
        "capacidad": capacidad,
        "pisos": datos.pisos,
        "filas": datos.filas,
        "asientos": capacidad,
        "estado": datos.estado,
    }


@router.patch("/buses/{bus_id}")
async def cambiar_estado_bus(
    bus_id: int,
    datos: BusEstadoIn,
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    resultado = await sesion.execute(
        text("UPDATE buses SET estado = :estado WHERE id = :id"),
        {"estado": datos.estado, "id": bus_id},
    )
    if resultado.rowcount == 0:
        await sesion.rollback()
        raise HTTPException(status_code=404, detail="Bus no encontrado")
    await sesion.commit()
    return {"id": bus_id, "estado": datos.estado}


@router.delete("/buses/{bus_id}", status_code=204)
async def borrar_bus(
    bus_id: int,
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    viajes = (
        await sesion.execute(text("SELECT COUNT(*) FROM viajes WHERE bus_id = :id"), {"id": bus_id})
    ).scalar_one()
    if int(viajes) > 0:
        raise HTTPException(status_code=409, detail="El bus tiene viajes y no se puede eliminar")
    try:
        await sesion.execute(text("DELETE FROM asientos WHERE bus_id = :id"), {"id": bus_id})
        resultado = await sesion.execute(text("DELETE FROM buses WHERE id = :id"), {"id": bus_id})
        if resultado.rowcount == 0:
            raise HTTPException(status_code=404, detail="Bus no encontrado")
        await sesion.commit()
    except HTTPException:
        await sesion.rollback()
        raise
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)


@router.get("/viajes")
async def listar_viajes_admin(
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT v.id, v.salida, v.llegada_est, v.precio, v.estado,
                       co.nombre AS origen, cd.nombre AS destino, b.numero_disco
                  FROM viajes v
                  JOIN rutas r ON r.id = v.ruta_id
                  JOIN ciudades co ON co.id = r.origen_id
                  JOIN ciudades cd ON cd.id = r.destino_id
                  JOIN buses b ON b.id = v.bus_id
                 WHERE v.salida >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                 ORDER BY v.salida
                 LIMIT 60
                """
            )
        )
    ).mappings().all()
    return [fila_a_dict(fila) for fila in filas]


@router.delete("/viajes/{viaje_id}")
async def cancelar_viaje(
    viaje_id: int,
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    ocupados = (
        await sesion.execute(
            text(
                """
                SELECT COUNT(*)
                  FROM boletos
                 WHERE viaje_id = :id AND estado IN ('reservado', 'pagado', 'usado')
                """
            ),
            {"id": viaje_id},
        )
    ).scalar_one()
    if int(ocupados) > 0:
        raise HTTPException(status_code=409, detail="El viaje tiene pasajes vigentes y no se puede cancelar")
    resultado = await sesion.execute(
        text("UPDATE viajes SET estado = 'cancelado' WHERE id = :id AND estado = 'programado'"),
        {"id": viaje_id},
    )
    if resultado.rowcount == 0:
        await sesion.rollback()
        raise HTTPException(status_code=404, detail="Viaje programado no encontrado")
    await sesion.commit()
    return {"id": viaje_id, "estado": "cancelado"}


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


@router.post("/horarios/generar")
async def generar_horario(_: dict = Depends(exigir_admin)):
    creados = await generar_salidas()
    return {"creados": creados, "dias": 30}
