"""Cálculo de tarifa y distancia del taxi. No consulta la base."""

import math
from datetime import datetime, time


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radio = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radio * math.asin(min(1.0, math.sqrt(a)))


def minutos_por_haversine(distancia_km: float, velocidad_kmh: float = 25.0) -> int:
    if distancia_km <= 0:
        return 1
    return max(1, int(round(distancia_km / velocidad_kmh * 60)))


def es_nocturno(momento: datetime, desde: time, hasta: time) -> bool:
    hora = momento.time().replace(microsecond=0)
    if desde == hasta:
        return False
    if desde < hasta:
        return desde <= hora < hasta
    return hora >= desde or hora < hasta


def estimar_tarifa(
    distancia_km: float,
    minutos: float,
    arranque: float,
    costo_km: float,
    costo_minuto: float,
    minima: float,
    recargo_pct: float = 0,
    nocturno: bool = False,
) -> float:
    bruto = float(arranque) + max(0.0, distancia_km) * float(costo_km) + max(0.0, minutos) * float(costo_minuto)
    if nocturno and recargo_pct:
        bruto *= 1 + float(recargo_pct) / 100
    return round(max(bruto, float(minima)), 2)


def mas_cercano(origen: tuple[float, float], conductores: list[dict]) -> dict | None:
    candidatos = []
    for conductor in conductores:
        if conductor.get("estado") != "disponible":
            continue
        if conductor.get("lat") is None or conductor.get("lng") is None:
            continue
        distancia = haversine_km(origen[0], origen[1], float(conductor["lat"]), float(conductor["lng"]))
        candidatos.append((distancia, conductor))
    if not candidatos:
        return None
    candidatos.sort(key=lambda item: (item[0], item[1]["id"]))
    elegido = dict(candidatos[0][1])
    elegido["distancia_km"] = round(candidatos[0][0], 3)
    return elegido


def coordenada_valida(lat: float, lng: float) -> bool:
    return -5.2 <= lat <= 1.7 and -81.5 <= lng <= -75.0
