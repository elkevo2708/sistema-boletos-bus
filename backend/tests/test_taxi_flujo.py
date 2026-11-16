"""Máquina de estados, código de verificación, calificación y permisos del taxi."""

import os
from secrets import token_hex

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


def test_estados_codigo_y_calificacion(admin):
    lat, lng = -0.928, -79.22
    pedido = admin.post(
        "/taxi/viajes",
        json={
            "origen_lat": lat,
            "origen_lng": lng,
            "destino_lat": lat + 0.01,
            "destino_lng": lng + 0.01,
            "destino_texto": "Prueba de estados",
            "metodo_pago": "efectivo",
            "pasajeros": 2,
            "servicio": "estandar",
        },
    )
    assert pedido.status_code == 201, pedido.text
    viaje = pedido.json()
    assert len(viaje["codigo"]) == 4
    viaje_id = viaje["id"]
    numero = str(viaje["conductor"]["unidad"]).removeprefix("E")
    conductor = _entrar(f"conductor.ejemplo{numero}@lamana.local", "Conductor123!")
    try:
        aceptado = conductor.post(f"/taxi/conductor/viajes/{viaje_id}/aceptar")
        assert aceptado.status_code == 200, aceptado.text
        ilegal = conductor.post(
            f"/taxi/conductor/viajes/{viaje_id}/estado",
            json={"estado": "a_bordo", "codigo": viaje["codigo"]},
        )
        assert ilegal.status_code == 409, ilegal.text
        assert conductor.post(f"/taxi/conductor/viajes/{viaje_id}/estado", json={"estado": "en_camino"}).status_code == 200
        assert conductor.post(f"/taxi/conductor/viajes/{viaje_id}/estado", json={"estado": "llego"}).status_code == 200
        malo = conductor.post(
            f"/taxi/conductor/viajes/{viaje_id}/estado",
            json={"estado": "a_bordo", "codigo": "0000" if viaje["codigo"] != "0000" else "1111"},
        )
        assert malo.status_code == 422, malo.text
        bueno = conductor.post(
            f"/taxi/conductor/viajes/{viaje_id}/estado",
            json={"estado": "a_bordo", "codigo": viaje["codigo"]},
        )
        assert bueno.status_code == 200, bueno.text
        assert bueno.json()["estado"] == "a_bordo"
        final = conductor.post(f"/taxi/conductor/viajes/{viaje_id}/estado", json={"estado": "finalizado"})
        assert final.status_code == 200, final.text
    finally:
        conductor.close()

    nota = admin.post(f"/taxi/viajes/{viaje_id}/calificar", json={"estrellas": 5, "comentario": "Bien", "propina": 1})
    assert nota.status_code == 200, nota.text
    assert nota.json()["calificacion"] == 5
    otra = admin.post(f"/taxi/viajes/{viaje_id}/calificar", json={"estrellas": 4})
    assert otra.status_code == 409


def test_otro_rol_no_ve_el_panel_ni_el_viaje(admin):
    marca = token_hex(4)
    with httpx.Client(base_url=BASE, timeout=30) as http:
        alta = http.post(
            "/auth/registro",
            json={
                "nombre": "Pasajero",
                "apellido": "Prueba",
                "documento": f"P{marca}",
                "email": f"pasajero.flujo.{marca}@gmail.com",
                "password": "Clave1234",
            },
        )
        assert alta.status_code == 201, alta.text
        http.headers["Authorization"] = f"Bearer {alta.json()['access_token']}"
        panel = http.get("/admin/taxi/sos")
        assert panel.status_code == 403
        ajeno = http.get("/taxi/viajes/1")
    assert ajeno.status_code in (403, 404)

    operador = _entrar("operador.transporte@lamana.local", "Operador123!")
    try:
        assert operador.get("/admin/taxi/reportes").status_code == 403
    finally:
        operador.close()
    assert admin.get("/admin/taxi/reportes").status_code == 200
    assert admin.get("/taxi/lugares").status_code == 200
