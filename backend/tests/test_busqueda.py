"""Búsqueda pública de salidas y fechas siguientes, detrás de /api."""

import os
from datetime import date, timedelta

import httpx
import pytest

BASE = os.environ.get("API_BASE", "http://127.0.0.1:8080/api")


@pytest.fixture(scope="module")
def cliente():
    with httpx.Client(base_url=BASE, timeout=60) as http:
        yield http


def _id(ciudades, nombre):
    return next(item["id"] for item in ciudades if item["nombre"] == nombre)


def test_hay_salidas_y_fechas_siguientes(cliente):
    ciudades = cliente.get("/ciudades")
    assert ciudades.status_code == 200, ciudades.text
    origen = _id(ciudades.json(), "La Maná")
    destino = _id(ciudades.json(), "Guayaquil")
    dentro = (date.today() + timedelta(days=3)).isoformat()
    viajes = cliente.get("/viajes", params={"origen": origen, "destino": destino, "fecha": dentro})
    assert viajes.status_code == 200, viajes.text
    assert len(viajes.json()) >= 1

    lejos = (date.today() + timedelta(days=120)).isoformat()
    vacio = cliente.get("/viajes", params={"origen": origen, "destino": destino, "fecha": lejos})
    assert vacio.status_code == 200, vacio.text
    assert vacio.json() == []

    proximas = cliente.get(
        "/viajes/proximas",
        params={"origen": origen, "destino": destino, "desde": lejos},
    )
    assert proximas.status_code == 200, proximas.text
    fechas = proximas.json()
    assert fechas
    assert all(item["salidas"] >= 1 for item in fechas)

    regreso = cliente.get("/viajes", params={"origen": destino, "destino": origen, "fecha": dentro})
    assert regreso.status_code == 200, regreso.text
    assert len(regreso.json()) >= 1


def test_generar_horario_es_idempotente(cliente):
    acceso = cliente.post(
        "/auth/login",
        data={"username": "admin@lamana.local", "password": "Admin123!"},
    )
    assert acceso.status_code == 200, acceso.text
    token = acceso.json()["access_token"]
    primero = cliente.post("/admin/horarios/generar", headers={"Authorization": f"Bearer {token}"})
    assert primero.status_code == 200, primero.text
    segundo = cliente.post("/admin/horarios/generar", headers={"Authorization": f"Bearer {token}"})
    assert segundo.status_code == 200, segundo.text
    assert segundo.json()["creados"] == 0
    assert segundo.json()["dias"] == 30
