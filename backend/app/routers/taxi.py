"""Taxis del cantón: solicitud, asignación al más cercano y tablero."""

import math
import secrets
from datetime import datetime, time, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencias import exigir_pasajero, exigir_taxi, obtener_sesion, usuario_actual
from app.errores import traducir_error_mysql
from app.limite import permitir
from app.taxi_logica import (
    coordenada_valida,
    es_nocturno,
    estimar_tarifa,
    haversine_km,
    minutos_por_haversine,
)
from app.tiempo import ahora_colombia
from app.ws import gestor_taxi

router = APIRouter()
CENTRO = (-0.9406, -79.2344)
AGENTE = "LaManaRecorres/1.0 (turismo@lamana.ec)"


def _num(valor):
    if valor is None:
        return None
    return float(valor)


def _publico_conductor(fila: dict | None) -> dict | None:
    if not fila or fila.get("conductor_id") is None and fila.get("id") is None:
        return None
    return {
        "id": fila.get("conductor_id") or fila.get("id"),
        "nombre": fila.get("nombre"),
        "unidad": fila.get("numero_unidad"),
        "placa": fila.get("placa"),
        "foto": fila.get("foto"),
        "telefono": fila.get("telefono"),
        "lat": _num(fila.get("lat")),
        "lng": _num(fila.get("lng")),
        "estado": fila.get("estado") or "disponible",
        "rumbo": int(fila["rumbo"]) if fila.get("rumbo") is not None else None,
        "distancia_km": _num(fila.get("km")) if fila.get("km") is not None else None,
    }


def _viaje(fila: dict, conductor: dict | None = None) -> dict:
    return {
        "id": fila["id"],
        "estado": fila["estado"],
        "origen": {"lat": _num(fila["origen_lat"]), "lng": _num(fila["origen_lng"])},
        "destino": {
            "lat": _num(fila["destino_lat"]),
            "lng": _num(fila["destino_lng"]),
            "texto": fila["destino_texto"],
        },
        "distancia_km": _num(fila["distancia_km"]),
        "duracion_min": fila["duracion_min"],
        "tarifa_estimada": _num(fila["tarifa_estimada"]),
        "tarifa_final": _num(fila["tarifa_final"]),
        "metodo_pago": fila["metodo_pago"],
        "pago_estado": fila["pago_estado"],
        "calificacion": fila["calificacion"],
        "comentario": fila["comentario"],
        "pasajero_nombre": fila.get("pasajero_nombre"),
        "conductor": conductor,
        "ejemplo_tarifa": True,
        "codigo": fila.get("codigo"),
        "pasajeros": int(fila.get("pasajeros") or 1),
        "nota": fila.get("nota") or "",
        "propina": None if fila.get("propina") is None else float(fila.get("propina") or 0),
        "servicio": fila.get("servicio") or "estandar",
        "seguimiento": fila.get("seguimiento"),
        "ofrecido_hasta": fila["ofrecido_hasta"].isoformat(sep=" ") if fila.get("ofrecido_hasta") else None,
    }


async def _broadcast(sesion: AsyncSession, viaje_id: int | None = None) -> None:
    taxis = (
        await sesion.execute(
            text(
                """
                SELECT c.id, c.lat, c.lng, c.numero_unidad, c.placa, c.estado, p.nombre AS compania
                  FROM taxi_conductores c
                  JOIN taxi_companias p ON p.id = c.compania_id
                 WHERE c.activo = 1 AND c.estado = 'disponible' AND c.lat IS NOT NULL
                """
            )
        )
    ).mappings().all()
    await gestor_taxi.emitir_flota(
        {
            "tipo": "flota",
            "taxis": [
                {
                    "id": fila["id"],
                    "lat": _num(fila["lat"]),
                    "lng": _num(fila["lng"]),
                    "unidad": fila["numero_unidad"],
                    "placa": fila["placa"],
                    "compania": fila["compania"],
                }
                for fila in taxis
            ],
        }
    )
    if viaje_id is not None:
        publico = await _leer_viaje(sesion, viaje_id)
        if publico is not None:
            publico.pop("codigo", None)
            await gestor_taxi.emitir_viaje(viaje_id, {"tipo": "viaje", "viaje": publico})


async def _leer_viaje(sesion: AsyncSession, viaje_id: int) -> dict | None:
    fila = (
        await sesion.execute(
            text(
                """
                SELECT v.*, u.nombre AS pasajero_nombre,
                       c.id AS conductor_id, cu.nombre AS nombre, cu.telefono AS telefono,
                       c.numero_unidad, c.placa, c.foto, c.lat, c.lng
                  FROM taxi_viajes v
                  JOIN usuarios u ON u.id = v.pasajero_id
                  LEFT JOIN taxi_conductores c ON c.id = COALESCE(v.conductor_id, v.ofrecido_conductor_id)
                  LEFT JOIN usuarios cu ON cu.id = c.usuario_id
                 WHERE v.id = :id
                """
            ),
            {"id": viaje_id},
        )
    ).mappings().first()
    if fila is None:
        return None
    conductor = None
    if fila["nombre"]:
        conductor = _publico_conductor(dict(fila))
    return _viaje(dict(fila), conductor)


async def _ruta(origen: tuple[float, float], destino: tuple[float, float]) -> dict:
    directa = haversine_km(origen[0], origen[1], destino[0], destino[1])
    respaldo = {
        "distancia_km": round(directa * 1.35, 3),
        "duracion_min": minutos_por_haversine(directa * 1.35),
        "geometria": None,
        "fuente": "haversine",
    }
    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{origen[1]},{origen[0]};{destino[1]},{destino[0]}?overview=simplified&geometries=geojson"
    )
    try:
        async with httpx.AsyncClient(timeout=4) as cliente:
            respuesta = await cliente.get(url, headers={"User-Agent": AGENTE})
        if respuesta.status_code != 200:
            return respaldo
        tramo = respuesta.json()["routes"][0]
        return {
            "distancia_km": round(tramo["distance"] / 1000, 3),
            "duracion_min": max(1, int(round(tramo["duration"] / 60))),
            "geometria": tramo.get("geometry"),
            "fuente": "osrm",
        }
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        return respaldo


async def _tarifa_activa(sesion: AsyncSession) -> dict:
    fila = (
        await sesion.execute(
            text(
                """
                SELECT t.*, c.nombre AS compania
                  FROM taxi_tarifas t
                  JOIN taxi_companias c ON c.id = t.compania_id
                 WHERE t.activa = 1 AND c.activa = 1
                 ORDER BY t.ejemplo, t.id
                 LIMIT 1
                """
            )
        )
    ).mappings().first()
    if fila is None:
        raise HTTPException(status_code=409, detail="No hay una tarifa de taxi configurada")
    return dict(fila)


def _como_hora(valor) -> time:
    if isinstance(valor, time):
        return valor
    if isinstance(valor, timedelta):
        segundos = int(valor.total_seconds()) % 86400
        return time(segundos // 3600, (segundos % 3600) // 60, segundos % 60)
    if isinstance(valor, datetime):
        return valor.time()
    partes = str(valor).split(":")
    return time(int(partes[0]), int(partes[1]), int(float(partes[2])) if len(partes) > 2 else 0)


def _precio(tarifa: dict, distancia_km: float, minutos: int) -> float:
    ahora = ahora_colombia()
    nocturno = es_nocturno(ahora, _como_hora(tarifa["noche_desde"]), _como_hora(tarifa["noche_hasta"]))
    return estimar_tarifa(
        distancia_km,
        minutos,
        tarifa["arranque"],
        tarifa["costo_km"],
        tarifa["costo_minuto"],
        tarifa["tarifa_minima"],
        tarifa["recargo_nocturno_pct"],
        nocturno,
    )


async def liberar_vencidas(sesion: AsyncSession) -> None:
    vencidos = (
        await sesion.execute(
            text(
                """
                SELECT id, ofrecido_conductor_id
                  FROM taxi_viajes
                 WHERE estado = 'solicitado'
                   AND ofrecido_conductor_id IS NOT NULL
                   AND ofrecido_hasta IS NOT NULL
                   AND ofrecido_hasta < NOW()
                 FOR UPDATE
                """
            )
        )
    ).mappings().all()
    for viaje in vencidos:
        await sesion.execute(
            text("INSERT IGNORE INTO taxi_rechazos (viaje_id, conductor_id) VALUES (:v, :c)"),
            {"v": viaje["id"], "c": viaje["ofrecido_conductor_id"]},
        )
        await sesion.execute(
            text("UPDATE taxi_conductores SET estado = 'disponible' WHERE id = :id AND estado = 'ocupado'"),
            {"id": viaje["ofrecido_conductor_id"]},
        )
        await sesion.execute(
            text("UPDATE taxi_viajes SET ofrecido_conductor_id = NULL, ofrecido_hasta = NULL WHERE id = :id"),
            {"id": viaje["id"]},
        )
        await asignar(sesion, viaje["id"])


async def asignar(sesion: AsyncSession, viaje_id: int) -> None:
    viaje = (
        await sesion.execute(text("SELECT * FROM taxi_viajes WHERE id = :id FOR UPDATE"), {"id": viaje_id})
    ).mappings().first()
    if viaje is None or viaje["estado"] != "solicitado":
        return
    lat, lng = float(viaje["origen_lat"]), float(viaje["origen_lng"])
    candidatos = (
        await sesion.execute(
            text(
                """
                SELECT c.id,
                       (6371 * ACOS(LEAST(1,
                          COS(RADIANS(:lat)) * COS(RADIANS(c.lat)) * COS(RADIANS(c.lng) - RADIANS(:lng))
                          + SIN(RADIANS(:lat)) * SIN(RADIANS(c.lat))
                       ))) AS km
                  FROM taxi_conductores c
                 WHERE c.activo = 1
                   AND c.estado = 'disponible'
                   AND c.lat IS NOT NULL
                   AND c.lng IS NOT NULL
                   AND c.lat BETWEEN :lat - 0.2 AND :lat + 0.2
                   AND c.lng BETWEEN :lng - 0.2 AND :lng + 0.2
                   AND c.ubicacion_en >= NOW() - INTERVAL 6 HOUR
                   AND NOT EXISTS (
                        SELECT 1 FROM taxi_rechazos r
                         WHERE r.viaje_id = :viaje AND r.conductor_id = c.id
                   )
                 ORDER BY km, c.id
                 LIMIT 8
                """
            ),
            {"lat": lat, "lng": lng, "viaje": viaje_id},
        )
    ).mappings().all()
    for candidato in candidatos:
        bloqueado = (
            await sesion.execute(
                text("SELECT id, estado, compania_id FROM taxi_conductores WHERE id = :id FOR UPDATE"),
                {"id": candidato["id"]},
            )
        ).mappings().first()
        if bloqueado is None or bloqueado["estado"] != "disponible":
            continue
        await sesion.execute(
            text("UPDATE taxi_conductores SET estado = 'ocupado' WHERE id = :id"),
            {"id": bloqueado["id"]},
        )
        await sesion.execute(
            text(
                """
                UPDATE taxi_viajes
                   SET ofrecido_conductor_id = :cid,
                       ofrecido_hasta = DATE_ADD(NOW(), INTERVAL 25 SECOND),
                       compania_id = :compania
                 WHERE id = :viaje
                """
            ),
            {"cid": bloqueado["id"], "compania": bloqueado["compania_id"], "viaje": viaje_id},
        )
        return
    await sesion.execute(
        text(
            """
            UPDATE taxi_viajes
               SET estado = 'cancelado', ofrecido_conductor_id = NULL, ofrecido_hasta = NULL
             WHERE id = :id AND estado = 'solicitado'
            """
        ),
        {"id": viaje_id},
    )


def _exigir_coords(lat: float, lng: float) -> None:
    if not coordenada_valida(lat, lng):
        raise HTTPException(status_code=422, detail="La coordenada está fuera del Ecuador")


@router.get("/taxi/cercanos")
async def cercanos(
    lat: float,
    lng: float,
    usuario: dict = Depends(exigir_pasajero),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    _exigir_coords(lat, lng)
    if not permitir(f"cercanos:{usuario['id']}", 30, 60):
        raise HTTPException(status_code=429, detail="Demasiadas consultas de taxis")
    filas = (
        await sesion.execute(
            text(
                """
                SELECT c.id, c.numero_unidad, c.placa, c.foto, c.lat, c.lng, c.estado, c.rumbo, u.nombre,
                       (6371 * ACOS(LEAST(1,
                          COS(RADIANS(:lat)) * COS(RADIANS(c.lat)) * COS(RADIANS(c.lng) - RADIANS(:lng))
                          + SIN(RADIANS(:lat)) * SIN(RADIANS(c.lat))
                       ))) AS km
                  FROM taxi_conductores c
                  JOIN usuarios u ON u.id = c.usuario_id
                 WHERE c.activo = 1 AND c.estado IN ('disponible', 'ocupado') AND c.lat IS NOT NULL
                   AND c.lat BETWEEN :lat - 0.2 AND :lat + 0.2
                   AND c.lng BETWEEN :lng - 0.2 AND :lng + 0.2
                   AND c.ubicacion_en >= NOW() - INTERVAL 6 HOUR
                 ORDER BY km, c.id
                 LIMIT 12
                """
            ),
            {"lat": lat, "lng": lng},
        )
    ).mappings().all()
    lista = []
    for fila in filas:
        item = _publico_conductor(dict(fila))
        item["eta_min"] = minutos_por_haversine(float(fila["km"]))
        item["distancia_km"] = round(float(fila["km"]), 3)
        lista.append(item)
    libres = [item for item in lista if item.get("estado") != "ocupado"]
    return {"taxis": lista, "mas_cercano": libres[0] if libres else None}


@router.get("/taxi/ruta")
async def ruta(
    origen_lat: float,
    origen_lng: float,
    destino_lat: float,
    destino_lng: float,
    _: dict = Depends(exigir_pasajero),
):
    _exigir_coords(origen_lat, origen_lng)
    _exigir_coords(destino_lat, destino_lng)
    return await _ruta((origen_lat, origen_lng), (destino_lat, destino_lng))


def _factor_servicio(servicio: str) -> float:
    return {"estandar": 1.0, "camioneta": 1.35}.get(servicio, 1.0)


@router.get("/taxi/cotizar")
async def cotizar(
    origen_lat: float,
    origen_lng: float,
    destino_lat: float,
    destino_lng: float,
    servicio: str = "estandar",
    _: dict = Depends(exigir_pasajero),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    _exigir_coords(origen_lat, origen_lng)
    _exigir_coords(destino_lat, destino_lng)
    if servicio not in ("estandar", "camioneta"):
        raise HTTPException(status_code=422, detail="El servicio es estándar o camioneta")
    trayecto = await _ruta((origen_lat, origen_lng), (destino_lat, destino_lng))
    tarifa = await _tarifa_activa(sesion)
    ahora = ahora_colombia()
    nocturno = es_nocturno(ahora, _como_hora(tarifa["noche_desde"]), _como_hora(tarifa["noche_hasta"]))
    precio = round(_precio(tarifa, trayecto["distancia_km"], trayecto["duracion_min"]) * _factor_servicio(servicio), 2)
    return {
        **trayecto,
        "tarifa_estimada": precio,
        "servicio": servicio,
        "ejemplo": bool(tarifa["ejemplo"]),
        "compania": tarifa["compania"],
        "nocturno": nocturno,
        "desglose": {
            "arranque": float(tarifa["arranque"]),
            "por_km": round(trayecto["distancia_km"] * float(tarifa["costo_km"]), 2),
            "por_minuto": round(trayecto["duracion_min"] * float(tarifa["costo_minuto"]), 2),
            "recargo_nocturno_pct": float(tarifa["recargo_nocturno_pct"]) if nocturno else 0,
            "factor_servicio": _factor_servicio(servicio),
            "minima": float(tarifa["tarifa_minima"]),
        },
        "aviso": "Tarifa de ejemplo, no es la tarifa oficial de una cooperativa.",
    }


@router.get("/taxi/geocodificar")
async def geocodificar(q: str, _: dict = Depends(exigir_pasajero)):
    consulta = q.strip()
    if len(consulta) < 3:
        raise HTTPException(status_code=422, detail="Escribe al menos 3 letras")
    if not permitir("nominatim", 1, 1.1):
        raise HTTPException(status_code=429, detail="Espera un segundo antes de otra búsqueda")
    try:
        async with httpx.AsyncClient(timeout=5) as cliente:
            respuesta = await cliente.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": f"{consulta}, La Maná, Ecuador", "format": "jsonv2", "limit": 5, "countrycodes": "ec"},
                headers={"User-Agent": AGENTE},
            )
        respuesta.raise_for_status()
        return [
            {"nombre": item.get("display_name"), "lat": float(item["lat"]), "lng": float(item["lon"])}
            for item in respuesta.json()
        ]
    except (httpx.HTTPError, KeyError, ValueError):
        lugares = (
            await _lugares_portal()
        )
        return [lugar for lugar in lugares if consulta.lower() in lugar["nombre"].lower()]


async def _lugares_portal() -> list[dict]:
    return [
        {"nombre": "Parque central de La Maná", "lat": CENTRO[0], "lng": CENTRO[1]},
        {"nombre": "Referencia del río San Pablo", "lat": -0.948, "lng": -79.228},
    ]


@router.post("/taxi/viajes", status_code=201)
async def solicitar(
    cuerpo: dict,
    usuario: dict = Depends(exigir_pasajero),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    if not permitir(f"solicitud:{usuario['id']}", 5, 600):
        raise HTTPException(status_code=429, detail="Demasiadas solicitudes de taxi")
    try:
        origen = (float(cuerpo["origen_lat"]), float(cuerpo["origen_lng"]))
        destino = (float(cuerpo["destino_lat"]), float(cuerpo["destino_lng"]))
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Origen y destino son coordenadas")
    _exigir_coords(*origen)
    _exigir_coords(*destino)
    metodo = cuerpo.get("metodo_pago") or "efectivo"
    if metodo not in ("efectivo", "deuna", "tarjeta", "payphone"):
        raise HTTPException(status_code=422, detail="Método de pago no reconocido")
    if metodo != "efectivo" and settings.pagos_modo != "sandbox":
        raise HTTPException(status_code=422, detail="En vivo el taxi se cobra en efectivo")
    servicio = cuerpo.get("servicio") or "estandar"
    if servicio not in ("estandar", "camioneta"):
        raise HTTPException(status_code=422, detail="El servicio es estándar o camioneta")
    try:
        pasajeros = int(cuerpo.get("pasajeros") or 1)
    except (TypeError, ValueError):
        pasajeros = 0
    if pasajeros < 1 or pasajeros > 6:
        raise HTTPException(status_code=422, detail="El taxi lleva de 1 a 6 pasajeros")
    trayecto = await _ruta(origen, destino)
    tarifa = await _tarifa_activa(sesion)
    precio = round(_precio(tarifa, trayecto["distancia_km"], trayecto["duracion_min"]) * _factor_servicio(servicio), 2)
    pago_estado = "no_aplica" if metodo == "efectivo" else "aprobado"
    try:
        await liberar_vencidas(sesion)
        resultado = await sesion.execute(
            text(
                """
                INSERT INTO taxi_viajes (
                  pasajero_id, compania_id, estado, origen_lat, origen_lng, destino_lat, destino_lng,
                  destino_texto, distancia_km, duracion_min, tarifa_estimada, metodo_pago, pago_estado,
                  codigo, pasajeros, nota, servicio, seguimiento
                ) VALUES (
                  :pasajero, :compania, 'solicitado', :olat, :olng, :dlat, :dlng,
                  :texto, :km, :minutos, :precio, :metodo, :pago,
                  :codigo, :pasajeros, :nota, :servicio, :seguimiento
                )
                """
            ),
            {
                "pasajero": usuario["id"],
                "compania": tarifa["compania_id"],
                "olat": origen[0],
                "olng": origen[1],
                "dlat": destino[0],
                "dlng": destino[1],
                "texto": str(cuerpo.get("destino_texto") or "")[:180],
                "km": trayecto["distancia_km"],
                "minutos": trayecto["duracion_min"],
                "precio": precio,
                "metodo": metodo,
                "pago": pago_estado,
                "codigo": f"{secrets.randbelow(10000):04d}",
                "pasajeros": pasajeros,
                "nota": str(cuerpo.get("nota") or "")[:180],
                "servicio": servicio,
                "seguimiento": secrets.token_hex(4),
            },
        )
        viaje_id = resultado.lastrowid
        await asignar(sesion, viaje_id)
        await sesion.commit()
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)
    publico = await _leer_viaje(sesion, viaje_id)
    await _broadcast(sesion, viaje_id)
    return publico


@router.get("/taxi/viajes/{viaje_id}")
async def ver_viaje(
    viaje_id: int,
    usuario: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    await liberar_vencidas(sesion)
    await sesion.commit()
    publico = await _leer_viaje(sesion, viaje_id)
    if publico is None:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    dueno = (
        await sesion.execute(text("SELECT pasajero_id, conductor_id FROM taxi_viajes WHERE id = :id"), {"id": viaje_id})
    ).mappings().first()
    conductor = (
        await sesion.execute(text("SELECT id FROM taxi_conductores WHERE usuario_id = :id"), {"id": usuario["id"]})
    ).mappings().first()
    es_pasajero = dueno["pasajero_id"] == usuario["id"]
    es_conductor = conductor is not None and dueno["conductor_id"] == conductor["id"]
    if not es_pasajero and not es_conductor and usuario["rol"] not in ("administrador", "operador_taxi"):
        raise HTTPException(status_code=403, detail="Este viaje no es tuyo")
    if not es_pasajero and usuario["rol"] not in ("administrador", "operador_taxi"):
        publico.pop("codigo", None)
    return publico


@router.post("/taxi/viajes/{viaje_id}/cancelar")
async def cancelar(
    viaje_id: int,
    usuario: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    viaje = (
        await sesion.execute(text("SELECT * FROM taxi_viajes WHERE id = :id FOR UPDATE"), {"id": viaje_id})
    ).mappings().first()
    if viaje is None or viaje["pasajero_id"] != usuario["id"]:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    if viaje["estado"] in ("a_bordo", "finalizado", "cancelado"):
        raise HTTPException(status_code=409, detail="Ese viaje ya no se puede cancelar")
    conductor_id = viaje["conductor_id"] or viaje["ofrecido_conductor_id"]
    await sesion.execute(
        text("UPDATE taxi_viajes SET estado = 'cancelado', ofrecido_hasta = NULL WHERE id = :id"),
        {"id": viaje_id},
    )
    if conductor_id:
        await sesion.execute(
            text("UPDATE taxi_conductores SET estado = 'disponible' WHERE id = :id AND estado = 'ocupado'"),
            {"id": conductor_id},
        )
    await sesion.commit()
    await _broadcast(sesion, viaje_id)
    return await _leer_viaje(sesion, viaje_id)


@router.post("/taxi/viajes/{viaje_id}/calificar")
async def calificar(
    viaje_id: int,
    cuerpo: dict,
    usuario: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    viaje = (
        await sesion.execute(text("SELECT * FROM taxi_viajes WHERE id = :id FOR UPDATE"), {"id": viaje_id})
    ).mappings().first()
    if viaje is None or viaje["pasajero_id"] != usuario["id"]:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    if viaje["estado"] != "finalizado" or viaje["calificacion"] is not None:
        raise HTTPException(status_code=409, detail="Este viaje no admite calificación")
    try:
        estrellas = int(cuerpo.get("estrellas"))
    except (TypeError, ValueError):
        estrellas = 0
    if estrellas < 1 or estrellas > 5:
        raise HTTPException(status_code=422, detail="La calificación va de 1 a 5")
    propina = cuerpo.get("propina")
    try:
        propina = None if propina in (None, "") else round(float(propina), 2)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="La propina debe ser un monto")
    if propina is not None and (propina < 0 or propina > 50):
        raise HTTPException(status_code=422, detail="La propina va de 0 a 50 dólares")
    await sesion.execute(
        text("UPDATE taxi_viajes SET calificacion = :e, comentario = :c, propina = :p WHERE id = :id"),
        {"e": estrellas, "c": str(cuerpo.get("comentario") or "")[:300], "p": propina, "id": viaje_id},
    )
    await sesion.commit()
    return await _leer_viaje(sesion, viaje_id)


async def _conductor_de(sesion: AsyncSession, usuario_id: int) -> dict:
    fila = (
        await sesion.execute(text("SELECT * FROM taxi_conductores WHERE usuario_id = :id"), {"id": usuario_id})
    ).mappings().first()
    if fila is None or not fila["activo"]:
        raise HTTPException(status_code=403, detail="Esta cuenta no tiene un taxi asignado")
    return dict(fila)


@router.post("/taxi/conductor/estado")
async def estado_conductor(
    cuerpo: dict,
    usuario: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    if usuario["rol"] != "conductor" and usuario["rol"] != "administrador":
        raise HTTPException(status_code=403, detail="Solo un conductor cambia su línea")
    conductor = await _conductor_de(sesion, usuario["id"])
    en_linea = bool(cuerpo.get("en_linea"))
    if en_linea and (conductor["lat"] is None or conductor["lng"] is None):
        raise HTTPException(status_code=422, detail="Primero envía tu ubicación")
    nuevo = "disponible" if en_linea else "fuera"
    if conductor["estado"] == "ocupado" and not en_linea:
        raise HTTPException(status_code=409, detail="Termina el viaje antes de salir de línea")
    await sesion.execute(
        text("UPDATE taxi_conductores SET estado = :estado WHERE id = :id"),
        {"estado": nuevo, "id": conductor["id"]},
    )
    await sesion.commit()
    await _broadcast(sesion)
    return {"estado": nuevo}


@router.post("/taxi/conductor/ubicacion")
async def ubicacion(
    cuerpo: dict,
    usuario: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    if not permitir(f"gps:{usuario['id']}", 1, 2):
        raise HTTPException(status_code=429, detail="La ubicación se actualiza cada dos segundos")
    conductor = await _conductor_de(sesion, usuario["id"])
    try:
        lat, lng = float(cuerpo["lat"]), float(cuerpo["lng"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Latitud y longitud numéricas")
    _exigir_coords(lat, lng)
    rumbo = cuerpo.get("rumbo")
    try:
        rumbo = int(rumbo) % 360 if rumbo is not None else conductor.get("rumbo")
    except (TypeError, ValueError):
        rumbo = conductor.get("rumbo")
    await sesion.execute(
        text("UPDATE taxi_conductores SET lat = :lat, lng = :lng, rumbo = :rumbo, ubicacion_en = NOW() WHERE id = :id"),
        {"lat": lat, "lng": lng, "rumbo": rumbo, "id": conductor["id"]},
    )
    await sesion.commit()
    await _broadcast(sesion)
    return {"ok": True}


@router.get("/taxi/conductor/viaje")
async def viaje_conductor(usuario: dict = Depends(usuario_actual), sesion: AsyncSession = Depends(obtener_sesion)):
    await liberar_vencidas(sesion)
    await sesion.commit()
    conductor = await _conductor_de(sesion, usuario["id"])
    fila = (
        await sesion.execute(
            text(
                """
                SELECT id FROM taxi_viajes
                 WHERE estado IN ('solicitado', 'asignado', 'en_camino', 'llego', 'a_bordo')
                   AND (conductor_id = :id OR ofrecido_conductor_id = :id)
                 ORDER BY id DESC
                 LIMIT 1
                """
            ),
            {"id": conductor["id"]},
        )
    ).mappings().first()
    if fila is None:
        return None
    publico = await _leer_viaje(sesion, fila["id"])
    if publico:
        publico.pop("codigo", None)
    return publico


@router.post("/taxi/conductor/viajes/{viaje_id}/aceptar")
async def aceptar(
    viaje_id: int,
    usuario: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    conductor = await _conductor_de(sesion, usuario["id"])
    viaje = (
        await sesion.execute(text("SELECT * FROM taxi_viajes WHERE id = :id FOR UPDATE"), {"id": viaje_id})
    ).mappings().first()
    if viaje is None:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    if viaje["ofrecido_conductor_id"] != conductor["id"] or viaje["estado"] != "solicitado":
        raise HTTPException(status_code=409, detail="Esta oferta ya no está disponible")
    bloqueado = (
        await sesion.execute(
            text("SELECT estado FROM taxi_conductores WHERE id = :id FOR UPDATE"),
            {"id": conductor["id"]},
        )
    ).mappings().first()
    activo = (
        await sesion.execute(
            text(
                """
                SELECT id FROM taxi_viajes
                 WHERE conductor_id = :id AND estado IN ('asignado', 'en_camino', 'llego', 'a_bordo')
                 FOR UPDATE
                """
            ),
            {"id": conductor["id"]},
        )
    ).first()
    if bloqueado is None or bloqueado["estado"] != "ocupado" or activo is not None:
        raise HTTPException(status_code=409, detail="No puedes aceptar dos viajes a la vez")
    await sesion.execute(
        text(
            """
            UPDATE taxi_viajes
               SET estado = 'asignado', conductor_id = :cid, ofrecido_hasta = NULL
             WHERE id = :id AND estado = 'solicitado' AND ofrecido_conductor_id = :cid
            """
        ),
        {"cid": conductor["id"], "id": viaje_id},
    )
    await sesion.commit()
    await _broadcast(sesion, viaje_id)
    publico = await _leer_viaje(sesion, viaje_id)
    if publico:
        publico.pop("codigo", None)
    return publico


@router.post("/taxi/conductor/viajes/{viaje_id}/rechazar")
async def rechazar(
    viaje_id: int,
    usuario: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    conductor = await _conductor_de(sesion, usuario["id"])
    viaje = (
        await sesion.execute(text("SELECT * FROM taxi_viajes WHERE id = :id FOR UPDATE"), {"id": viaje_id})
    ).mappings().first()
    if viaje is None or viaje["ofrecido_conductor_id"] != conductor["id"] or viaje["estado"] != "solicitado":
        raise HTTPException(status_code=409, detail="Esta oferta ya no está disponible")
    await sesion.execute(
        text("INSERT IGNORE INTO taxi_rechazos (viaje_id, conductor_id) VALUES (:v, :c)"),
        {"v": viaje_id, "c": conductor["id"]},
    )
    await sesion.execute(
        text("UPDATE taxi_conductores SET estado = 'disponible' WHERE id = :id"),
        {"id": conductor["id"]},
    )
    await sesion.execute(
        text("UPDATE taxi_viajes SET ofrecido_conductor_id = NULL, ofrecido_hasta = NULL WHERE id = :id"),
        {"id": viaje_id},
    )
    await asignar(sesion, viaje_id)
    await sesion.commit()
    await _broadcast(sesion, viaje_id)
    publico = await _leer_viaje(sesion, viaje_id)
    if publico:
        publico.pop("codigo", None)
    return publico


@router.post("/taxi/conductor/viajes/{viaje_id}/estado")
async def avanzar(
    viaje_id: int,
    cuerpo: dict,
    usuario: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    conductor = await _conductor_de(sesion, usuario["id"])
    destino = cuerpo.get("estado")
    viaje = (
        await sesion.execute(text("SELECT * FROM taxi_viajes WHERE id = :id FOR UPDATE"), {"id": viaje_id})
    ).mappings().first()
    if viaje is None or viaje["conductor_id"] != conductor["id"]:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    orden = {"asignado": "en_camino", "en_camino": "llego", "llego": "a_bordo", "a_bordo": "finalizado"}
    if orden.get(viaje["estado"]) != destino:
        raise HTTPException(status_code=409, detail="Ese cambio de estado no corresponde")
    if destino == "a_bordo" and str(cuerpo.get("codigo") or "") != str(viaje.get("codigo") or ""):
        raise HTTPException(status_code=422, detail="El código de verificación no coincide")
    if destino == "finalizado":
        await sesion.execute(
            text(
                """
                UPDATE taxi_viajes
                   SET estado = 'finalizado', tarifa_final = tarifa_estimada
                 WHERE id = :id
                """
            ),
            {"id": viaje_id},
        )
        await sesion.execute(
            text("UPDATE taxi_conductores SET estado = 'disponible' WHERE id = :id"),
            {"id": conductor["id"]},
        )
    else:
        await sesion.execute(
            text("UPDATE taxi_viajes SET estado = :estado WHERE id = :id"),
            {"estado": destino, "id": viaje_id},
        )
    await sesion.commit()
    await _broadcast(sesion, viaje_id)
    publico = await _leer_viaje(sesion, viaje_id)
    if publico:
        publico.pop("codigo", None)
    return publico


@router.post("/taxi/demo/simular")
async def simular(_: dict = Depends(exigir_pasajero), sesion: AsyncSession = Depends(obtener_sesion)):
    if settings.pagos_modo != "sandbox":
        raise HTTPException(status_code=404, detail="El simulador solo existe en modo de prueba")
    filas = (
        await sesion.execute(
            text("SELECT id FROM taxi_conductores WHERE ejemplo = 1 AND activo = 1 ORDER BY id")
        )
    ).all()
    fase = getattr(simular, "fase", 0) + 0.35
    simular.fase = fase
    for indice, fila in enumerate(filas):
        angulo = fase + indice * (math.tau / max(1, len(filas)))
        lat = CENTRO[0] + 0.004 * math.cos(angulo)
        lng = CENTRO[1] + 0.004 * math.sin(angulo)
        rumbo = int((math.degrees(angulo) + 90) % 360)
        await sesion.execute(
            text(
                """
                UPDATE taxi_conductores
                   SET lat = :lat, lng = :lng, rumbo = :rumbo, ubicacion_en = NOW(),
                       estado = IF(estado = 'fuera', 'disponible', estado)
                 WHERE id = :id AND estado <> 'ocupado'
                """
            ),
            {"lat": round(lat, 6), "lng": round(lng, 6), "rumbo": rumbo, "id": fila[0]},
        )
    await sesion.commit()
    await _broadcast(sesion)
    return {"movidos": len(filas), "centro": {"lat": CENTRO[0], "lng": CENTRO[1]}, "ejemplo": True}


@router.get("/admin/taxi/resumen")
async def resumen_taxi(_: dict = Depends(exigir_taxi), sesion: AsyncSession = Depends(obtener_sesion)):
    def uno(sql: str) -> str:
        return sql

    companias = (await sesion.execute(text("SELECT COUNT(*) FROM taxi_companias WHERE activa = 1"))).scalar_one()
    disponibles = (
        await sesion.execute(text("SELECT COUNT(*) FROM taxi_conductores WHERE activo = 1 AND estado = 'disponible'"))
    ).scalar_one()
    viajes = (
        await sesion.execute(text("SELECT COUNT(*) FROM taxi_viajes WHERE DATE(creado_en) = CURDATE()"))
    ).scalar_one()
    finalizados = (
        await sesion.execute(
            text("SELECT COUNT(*) FROM taxi_viajes WHERE estado = 'finalizado' AND DATE(actualizado_en) = CURDATE()")
        )
    ).scalar_one()
    flota = (
        await sesion.execute(
            text(
                """
                SELECT c.id, c.numero_unidad, c.placa, c.estado, c.lat, c.lng, c.rumbo, c.ejemplo, u.nombre, p.nombre AS compania
                  FROM taxi_conductores c
                  JOIN usuarios u ON u.id = c.usuario_id
                  JOIN taxi_companias p ON p.id = c.compania_id
                 WHERE c.activo = 1
                 ORDER BY c.estado, c.numero_unidad
                """
            )
        )
    ).mappings().all()
    return {
        "companias": int(companias),
        "disponibles": int(disponibles),
        "viajes_hoy": int(viajes),
        "finalizados_hoy": int(finalizados),
        "flota": [
            {
                "id": fila["id"],
                "nombre": fila["nombre"],
                "unidad": fila["numero_unidad"],
                "placa": fila["placa"],
                "estado": fila["estado"],
                "lat": _num(fila["lat"]),
                "lng": _num(fila["lng"]),
                "rumbo": int(fila["rumbo"]) if fila["rumbo"] is not None else None,
                "compania": fila["compania"],
                "ejemplo": bool(fila["ejemplo"]),
            }
            for fila in flota
        ],
    }


@router.get("/admin/taxi/companias")
async def listar_companias(_: dict = Depends(exigir_taxi), sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT c.id, c.nombre, c.ejemplo, t.arranque, t.costo_km, t.costo_minuto, t.tarifa_minima,
                       t.recargo_nocturno_pct, t.ejemplo AS tarifa_ejemplo, t.id AS tarifa_id
                  FROM taxi_companias c
                  LEFT JOIN taxi_tarifas t ON t.compania_id = c.id AND t.activa = 1
                 ORDER BY c.id
                """
            )
        )
    ).mappings().all()
    return [
        {
            "id": fila["id"],
            "nombre": fila["nombre"],
            "ejemplo": bool(fila["ejemplo"]),
            "arranque": float(fila["arranque"] or 0),
            "costo_km": float(fila["costo_km"] or 0),
            "costo_minuto": float(fila["costo_minuto"] or 0),
            "tarifa_minima": float(fila["tarifa_minima"] or 0),
            "recargo_nocturno_pct": float(fila["recargo_nocturno_pct"] or 0),
            "tarifa_ejemplo": bool(fila["tarifa_ejemplo"]),
            "tarifa_id": fila["tarifa_id"],
        }
        for fila in filas
    ]


@router.patch("/admin/taxi/tarifas/{tarifa_id}")
async def editar_tarifa(
    tarifa_id: int,
    cuerpo: dict,
    _: dict = Depends(exigir_taxi),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    campos = ["arranque", "costo_km", "costo_minuto", "tarifa_minima", "recargo_nocturno_pct"]
    valores = {}
    for campo in campos:
        if campo in cuerpo:
            valores[campo] = float(cuerpo[campo])
    if not valores:
        raise HTTPException(status_code=422, detail="No hay montos para guardar")
    asignaciones = ", ".join(f"{campo} = :{campo}" for campo in valores)
    valores["id"] = tarifa_id
    await sesion.execute(text(f"UPDATE taxi_tarifas SET {asignaciones} WHERE id = :id"), valores)
    await sesion.commit()
    return {"id": tarifa_id, **{campo: valores[campo] for campo in campos if campo in valores}}


@router.get("/admin/taxi/viajes")
async def historial(_: dict = Depends(exigir_taxi), sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT v.id, v.estado, v.tarifa_estimada, v.tarifa_final, v.metodo_pago, v.calificacion,
                       v.destino_texto, v.creado_en, u.nombre AS pasajero, c.numero_unidad
                  FROM taxi_viajes v
                  JOIN usuarios u ON u.id = v.pasajero_id
                  LEFT JOIN taxi_conductores c ON c.id = v.conductor_id
                 ORDER BY v.id DESC
                 LIMIT 40
                """
            )
        )
    ).mappings().all()
    return [
        {
            "id": fila["id"],
            "estado": fila["estado"],
            "tarifa_estimada": float(fila["tarifa_estimada"] or 0),
            "tarifa_final": float(fila["tarifa_final"]) if fila["tarifa_final"] is not None else None,
            "metodo_pago": fila["metodo_pago"],
            "calificacion": fila["calificacion"],
            "destino_texto": fila["destino_texto"],
            "creado_en": fila["creado_en"].isoformat() if fila["creado_en"] else None,
            "pasajero": fila["pasajero"],
            "numero_unidad": fila["numero_unidad"],
        }
        for fila in filas
    ]


@router.get("/taxi/lugares")
async def lugares(_: dict = Depends(exigir_pasajero), sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text("SELECT id, nombre, tipo, lat, lng FROM taxi_lugares ORDER BY tipo, nombre LIMIT 40")
        )
    ).mappings().all()
    return [{"id": f["id"], "nombre": f["nombre"], "tipo": f["tipo"], "lat": float(f["lat"]), "lng": float(f["lng"])} for f in filas]


@router.get("/taxi/servicios")
async def servicios(_: dict = Depends(exigir_pasajero)):
    return [
        {"codigo": "estandar", "nombre": "Estándar", "factor": 1},
        {"codigo": "camioneta", "nombre": "Camioneta", "factor": 1.35, "nota": "Ejemplo: recargo sobre la tarifa base"},
    ]


@router.get("/taxi/guardados")
async def guardados(usuario: dict = Depends(exigir_pasajero), sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text("SELECT id, etiqueta, texto, lat, lng FROM taxi_guardados WHERE usuario_id = :u ORDER BY etiqueta"),
            {"u": usuario["id"]},
        )
    ).mappings().all()
    return [{"id": f["id"], "etiqueta": f["etiqueta"], "texto": f["texto"], "lat": float(f["lat"]), "lng": float(f["lng"])} for f in filas]


@router.post("/taxi/guardados", status_code=201)
async def guardar_lugar(cuerpo: dict, usuario: dict = Depends(exigir_pasajero), sesion: AsyncSession = Depends(obtener_sesion)):
    etiqueta = (cuerpo.get("etiqueta") or "").strip().lower()
    if etiqueta not in ("casa", "trabajo"):
        raise HTTPException(status_code=422, detail="La etiqueta es casa o trabajo")
    try:
        lat, lng = float(cuerpo["lat"]), float(cuerpo["lng"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Latitud y longitud numéricas")
    _exigir_coords(lat, lng)
    await sesion.execute(
        text(
            """
            INSERT INTO taxi_guardados (usuario_id, etiqueta, texto, lat, lng)
            VALUES (:u, :e, :t, :lat, :lng)
            ON DUPLICATE KEY UPDATE texto = VALUES(texto), lat = VALUES(lat), lng = VALUES(lng)
            """
        ),
        {"u": usuario["id"], "e": etiqueta, "t": str(cuerpo.get("texto") or etiqueta)[:120], "lat": lat, "lng": lng},
    )
    await sesion.commit()
    return {"etiqueta": etiqueta}


@router.get("/taxi/mis-viajes")
async def mis_viajes(usuario: dict = Depends(exigir_pasajero), sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT id, estado, destino_texto, tarifa_estimada, tarifa_final, propina, calificacion, creado_en, servicio
                  FROM taxi_viajes WHERE pasajero_id = :u ORDER BY id DESC LIMIT 20
                """
            ),
            {"u": usuario["id"]},
        )
    ).mappings().all()
    return [
        {
            "id": f["id"],
            "estado": f["estado"],
            "destino_texto": f["destino_texto"],
            "tarifa_estimada": float(f["tarifa_estimada"] or 0),
            "tarifa_final": None if f["tarifa_final"] is None else float(f["tarifa_final"]),
            "propina": None if f["propina"] is None else float(f["propina"]),
            "calificacion": f["calificacion"],
            "servicio": f["servicio"],
            "creado_en": f["creado_en"].isoformat() if f["creado_en"] else None,
        }
        for f in filas
    ]


@router.get("/taxi/seguimiento/{token}")
async def seguimiento(token: str, sesion: AsyncSession = Depends(obtener_sesion)):
    fila = (
        await sesion.execute(text("SELECT id FROM taxi_viajes WHERE seguimiento = :t"), {"t": token[:16]})
    ).first()
    if fila is None:
        raise HTTPException(status_code=404, detail="No encontramos ese viaje")
    publico = await _leer_viaje(sesion, fila[0])
    if publico:
        publico.pop("codigo", None)
        if publico.get("conductor"):
            publico["conductor"].pop("telefono", None)
    return publico


@router.post("/taxi/sos", status_code=201)
async def sos(cuerpo: dict, usuario: dict = Depends(exigir_pasajero), sesion: AsyncSession = Depends(obtener_sesion)):
    try:
        lat, lng = float(cuerpo["lat"]), float(cuerpo["lng"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Latitud y longitud numéricas")
    _exigir_coords(lat, lng)
    await sesion.execute(
        text("INSERT INTO taxi_sos (usuario_id, viaje_id, lat, lng) VALUES (:u, :v, :lat, :lng)"),
        {"u": usuario["id"], "v": cuerpo.get("viaje_id"), "lat": lat, "lng": lng},
    )
    await sesion.commit()
    return {"emergencia": "911", "lat": lat, "lng": lng}


@router.get("/taxi/conductor/ganancias")
async def ganancias(usuario: dict = Depends(usuario_actual), sesion: AsyncSession = Depends(obtener_sesion)):
    conductor = await _conductor_de(sesion, usuario["id"])
    fila = (
        await sesion.execute(
            text(
                """
                SELECT
                  COALESCE(SUM(CASE WHEN DATE(creado_en) = CURDATE() THEN COALESCE(tarifa_final, tarifa_estimada) END), 0) AS hoy,
                  COALESCE(SUM(CASE WHEN creado_en >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) THEN COALESCE(tarifa_final, tarifa_estimada) END), 0) AS semana,
                  COUNT(*) AS viajes,
                  ROUND(AVG(calificacion), 1) AS nota
                  FROM taxi_viajes
                 WHERE conductor_id = :id AND estado = 'finalizado'
                """
            ),
            {"id": conductor["id"]},
        )
    ).mappings().one()
    return {"hoy": float(fila["hoy"]), "semana": float(fila["semana"]), "viajes": int(fila["viajes"]), "nota": fila["nota"]}


@router.get("/admin/taxi/sos")
async def listar_sos(_: dict = Depends(exigir_taxi), sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT s.id, s.lat, s.lng, s.viaje_id, s.creado_en, u.nombre
                  FROM taxi_sos s JOIN usuarios u ON u.id = s.usuario_id
                 ORDER BY s.id DESC LIMIT 30
                """
            )
        )
    ).mappings().all()
    return [
        {
            "id": f["id"],
            "lat": float(f["lat"]),
            "lng": float(f["lng"]),
            "viaje_id": f["viaje_id"],
            "nombre": f["nombre"],
            "creado_en": f["creado_en"].isoformat() if f["creado_en"] else None,
        }
        for f in filas
    ]


@router.get("/admin/taxi/reportes")
async def reportes(_: dict = Depends(exigir_taxi), sesion: AsyncSession = Depends(obtener_sesion)):
    por_dia = (
        await sesion.execute(
            text(
                """
                SELECT DATE(creado_en) AS dia, COUNT(*) AS viajes,
                       COALESCE(SUM(COALESCE(tarifa_final, tarifa_estimada)), 0) AS ingresos
                  FROM taxi_viajes
                 WHERE estado = 'finalizado' AND creado_en >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
                 GROUP BY DATE(creado_en) ORDER BY dia
                """
            )
        )
    ).mappings().all()
    return {"por_dia": [{"dia": str(f["dia"]), "viajes": int(f["viajes"]), "ingresos": float(f["ingresos"])} for f in por_dia]}
