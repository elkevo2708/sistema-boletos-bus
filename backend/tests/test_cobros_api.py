"""Cobros, portada y consulta de cédula contra el API publicado en /api."""

import hashlib
import hmac
import json
import os
from datetime import date, timedelta

import httpx
import pytest

BASE = os.environ.get("API_BASE", "http://127.0.0.1:8080/api")
SECRETO = "lamana-sandbox-firma"


def firmar(cuerpo: bytes) -> str:
    return hmac.new(SECRETO.encode(), cuerpo, hashlib.sha256).hexdigest()


@pytest.fixture(scope="module")
def admin():
    with httpx.Client(base_url=BASE, timeout=60) as http:
        acceso = http.post("/auth/login", data={"username": "admin@lamana.local", "password": "Admin123!"})
        assert acceso.status_code == 200, acceso.text
        http.headers["Authorization"] = f"Bearer {acceso.json()['access_token']}"
        yield http


def test_solo_tres_metodos_y_se_pueden_apagar(admin):
    lista = admin.get("/pagos/metodos")
    assert lista.status_code == 200, lista.text
    codigos = [item["codigo"] for item in lista.json()]
    assert codigos == ["deuna", "tarjeta", "payphone"]
    assert "transferencia" not in lista.text
    assert "efectivo" not in lista.text

    apagado = admin.patch("/admin/pagos/metodos/payphone", json={"activo": False})
    assert apagado.status_code == 200, apagado.text
    assert apagado.json()["modo"] == "sandbox"
    assert apagado.json()["credenciales_listas"] is False
    try:
        publicos = [item["codigo"] for item in admin.get("/pagos/metodos").json()]
        assert publicos == ["deuna", "tarjeta"]
    finally:
        encendido = admin.patch("/admin/pagos/metodos/payphone", json={"activo": True})
        assert encendido.status_code == 200

    viejo = admin.post(
        "/boletos/NOEXISTE/pagar",
        json={
            "referencia_ext": "TRF-1234",
            "metodo": "transferencia",
            "facturacion": {
                "tipo": "cedula",
                "identificacion": "1710034065",
                "razon_social": "MARÍA CEDEÑO PAREDES",
                "direccion": "La Maná",
            },
        },
    )
    assert viejo.status_code == 422


def test_cedulas_de_demostracion(admin):
    maria = admin.get("/facturacion/consulta", params={"tipo": "cedula", "identificacion": "1710034065"})
    assert maria.status_code == 200, maria.text
    assert maria.json()["razon_social"] == "MARÍA CEDEÑO PAREDES"
    jose = admin.get("/facturacion/consulta", params={"tipo": "cedula", "identificacion": "0926687856"})
    assert jose.status_code == 200, jose.text
    assert jose.json()["encontrado"] is True
    assert jose.json()["razon_social"] == "JOSÉ ANDRADE MERA"
    assert jose.json()["origen"] == "demo"
    ruc = admin.get("/facturacion/consulta", params={"tipo": "ruc", "identificacion": "1710034065001"})
    assert ruc.json()["encontrado"] is True
    vacio = admin.get("/facturacion/consulta", params={"tipo": "cedula", "identificacion": "0912345675"})
    assert vacio.status_code == 200, vacio.text
    assert vacio.json()["encontrado"] is False


def test_portada_conserva_la_foto_del_bus(admin):
    publica = admin.get("/portada")
    assert publica.status_code == 200, publica.text
    assert any(item["url"] == "/bus-lamana.jpg" and item["tipo"] == "imagen" for item in publica.json())
    creada = admin.post(
        "/admin/portada",
        data={
            "tipo": "video",
            "origen": "enlace",
            "titulo": "Video de prueba de la portada",
            "subtitulo": "Se reproduce en el inicio",
            "texto_boton": "Ver salidas",
            "enlace_boton": "/#buscar",
            "enlace": "https://youtu.be/dQw4w9WgXcQ",
            "orden": "9",
            "activo": "0",
        },
    )
    assert creada.status_code == 201, creada.text
    assert "youtube-nocookie.com/embed/dQw4w9WgXcQ" in creada.json()["incrustado"]
    admin.delete(f"/admin/portada/{creada.json()['id']}")


def test_webhook_deuna_es_idempotente():
    marca = hashlib.sha1(os.urandom(8)).hexdigest()[:8]
    with httpx.Client(base_url=BASE, timeout=60) as http:
        alta = http.post(
            "/auth/registro",
            json={
                "nombre": "Pago",
                "apellido": "Prueba",
                "documento": f"P{marca}",
                "email": f"pago.{marca}@gmail.com",
                "password": "Clave1234",
            },
        )
        assert alta.status_code == 201, alta.text
        token = alta.json()["access_token"]
        http.headers["Authorization"] = f"Bearer {token}"
        ciudades = http.get("/ciudades").json()
        origen = next(item["id"] for item in ciudades if item["nombre"] == "La Maná")
        destino = next(item["id"] for item in ciudades if item["nombre"] == "Quevedo")
        cuando = (date.today() + timedelta(days=4)).isoformat()
        viajes = http.get("/viajes", params={"origen": origen, "destino": destino, "fecha": cuando})
        assert viajes.status_code == 200 and viajes.json(), viajes.text
        viaje = viajes.json()[0]
        respuesta = http.get(f"/viajes/{viaje['id']}/asientos").json()
        asientos = respuesta["asientos"]
        libre = next(item for item in asientos if item["estado"] == "libre")
        reserva = http.post(
            "/boletos/reservar",
            json={
                "viaje_id": viaje["id"],
                "asiento_id": libre["id"],
                "pasajero_nombre": "Pago Prueba",
                "pasajero_documento": "1710034065",
            },
        )
        assert reserva.status_code == 201, reserva.text
        codigo = reserva.json()["codigo"].strip()
        referencia = f"DUNA-{marca}"
        preparado = http.post(
            f"/boletos/{codigo}/preparar",
            json={
                "referencia_ext": referencia,
                "metodo": "deuna",
                "facturacion": {
                    "tipo": "cedula",
                    "identificacion": "1710034065",
                    "razon_social": "MARÍA CEDEÑO PAREDES",
                    "direccion": "La Maná, Cotopaxi",
                    "email": "maria.cedeno@gmail.com",
                },
            },
        )
        assert preparado.status_code == 200, preparado.text
        assert preparado.json()["estado"] == "pendiente"
        cuerpo = json.dumps({"clientTransactionId": referencia, "status": "approved"}).encode()
        firma = firmar(cuerpo)
        primero = http.post("/pagos/webhooks/deuna", content=cuerpo, headers={"X-Deuna-Signature": firma, "Content-Type": "application/json"})
        assert primero.status_code == 200, primero.text
        assert primero.json()["repetido"] is False
        assert primero.json()["estado"] == "aprobado"
        segundo = http.post("/pagos/webhooks/deuna", content=cuerpo, headers={"X-Deuna-Signature": firma, "Content-Type": "application/json"})
        assert segundo.status_code == 200, segundo.text
        assert segundo.json()["repetido"] is True
        sin_firma = http.post("/pagos/webhooks/deuna", content=cuerpo, headers={"Content-Type": "application/json"})
        assert sin_firma.status_code == 401
