"""Asignación del taxi más cercano y un solo aceptador."""

import os
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

BASE = os.environ.get("API_BASE", "http://127.0.0.1:8080/api")


def _entrar(email, password):
    cliente = httpx.Client(base_url=BASE, timeout=60)
    acceso = cliente.post("/auth/login", data={"username": email, "password": password})
    assert acceso.status_code == 200, acceso.text
    cliente.headers["Authorization"] = f"Bearer {acceso.json()['access_token']}"
    return cliente


@pytest.fixture(scope="module")
def admin():
    cliente = _entrar("admin@lamana.local", "Admin123!")
    yield cliente
    cliente.close()


def _posicion(numero):
    return -0.9406 + numero * 0.0012, -79.2344 + numero * 0.0008


def test_cotizacion_avisa_que_es_ejemplo(admin):
    lat, lng = _posicion(6)
    cotizacion = admin.get(
        "/taxi/cotizar",
        params={"origen_lat": lat, "origen_lng": lng, "destino_lat": lat + 0.01, "destino_lng": lng + 0.01},
    )
    assert cotizacion.status_code == 200, cotizacion.text
    cuerpo = cotizacion.json()
    assert cuerpo["ejemplo"] is True
    assert cuerpo["tarifa_estimada"] >= 1.25
    assert "ejemplo" in cuerpo["aviso"].lower()


def test_asigna_al_mas_cercano_y_solo_uno_acepta(admin):
    lat, lng = _posicion(6)
    cercanos = admin.get("/taxi/cercanos", params={"lat": lat, "lng": lng})
    assert cercanos.status_code == 200, cercanos.text
    cercano = cercanos.json()["mas_cercano"]
    assert cercano is not None
    numero = str(cercano["unidad"]).removeprefix("E")
    pedido = admin.post(
        "/taxi/viajes",
        json={
            "origen_lat": lat,
            "origen_lng": lng,
            "destino_lat": lat + 0.008,
            "destino_lng": lng + 0.008,
            "destino_texto": "Prueba de asignación",
            "metodo_pago": "efectivo",
        },
    )
    assert pedido.status_code == 201, pedido.text
    viaje = pedido.json()
    assert viaje["estado"] == "solicitado"
    assert viaje["conductor"]["unidad"] == cercano["unidad"]
    viaje_id = viaje["id"]

    def aceptar():
        conductor = _entrar(f"conductor.ejemplo{numero}@lamana.local", "Conductor123!")
        try:
            return conductor.post(f"/taxi/conductor/viajes/{viaje_id}/aceptar")
        finally:
            conductor.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = [futuro.result() for futuro in (pool.submit(aceptar), pool.submit(aceptar))]
    codigos = sorted(item.status_code for item in resultados)
    assert codigos == [200, 409]
    ganador = next(item for item in resultados if item.status_code == 200)
    assert ganador.json()["estado"] == "asignado"
    admin.post(f"/taxi/viajes/{viaje_id}/cancelar")
