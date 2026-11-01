"""Portal de turismo contra el API publicado en /api."""

import os

import httpx
import pytest

BASE = os.environ.get("API_BASE", "http://127.0.0.1:8080/api")


@pytest.fixture(scope="module")
def admin():
    with httpx.Client(base_url=BASE, timeout=60) as http:
        acceso = http.post("/auth/login", data={"username": "admin@lamana.local", "password": "Admin123!"})
        assert acceso.status_code == 200, acceso.text
        http.headers["Authorization"] = f"Bearer {acceso.json()['access_token']}"
        yield http


def test_fichas_de_la_mana():
    with httpx.Client(base_url=BASE, timeout=30) as http:
        atractivos = http.get("/turismo/fichas", params={"tipo": "atractivo"})
        assert atractivos.status_code == 200, atractivos.text
        nombres = " ".join(item["nombre"] for item in atractivos.json())
        assert "San Pablo" in nombres
        assert "Zapanal" in nombres
        parroquias = http.get("/turismo/fichas", params={"tipo": "parroquia"}).json()
        assert {item["slug"] for item in parroquias} >= {"la-mana", "guasaganda", "pucayacu", "el-carmen"}
        portada = http.get("/portada", params={"ambito": "portal"})
        assert portada.status_code == 200
        assert any("subtrópico" in item["titulo"] or "subtropico" in item["titulo"].lower() for item in portada.json())
        bus = http.get("/portada", params={"ambito": "transporte"})
        assert any(item["url"] == "/bus-lamana.jpg" for item in bus.json())


def test_contacto_queda_registrado():
    with httpx.Client(base_url=BASE, timeout=30) as http:
        alta = http.post(
            "/turismo/contacto",
            json={"nombre": "Ana Pérez", "email": "ana.portal@gmail.com", "mensaje": "Quiero saber cómo llegar al río."},
        )
        assert alta.status_code == 201, alta.text
        assert alta.json()["estado"] == "recibido"


def test_admin_crea_y_borra_categoria(admin):
    alta = admin.post(
        "/admin/turismo/categorias",
        json={"tipo": "atractivo", "nombre": "Prueba miradores", "resumen": "Temporal de la prueba", "orden": 9},
    )
    assert alta.status_code == 201, alta.text
    categoria_id = alta.json()["id"]
    ficha = None
    try:
        ficha = admin.post(
            "/admin/turismo/fichas",
            json={
                "tipo": "atractivo",
                "categoria_id": categoria_id,
                "nombre": "Prueba salto de prueba",
                "resumen": "Ficha temporal que no debe quedar publicada.",
                "cuerpo": "Texto de prueba para el alta de turismo.",
                "activo": False,
            },
        )
        assert ficha.status_code == 201, ficha.text
        publicas = admin.get("/turismo/fichas", params={"q": "salto de prueba"}).json()
        assert publicas == []
    finally:
        if ficha is not None and ficha.status_code == 201:
            admin.delete(f"/admin/turismo/fichas/{ficha.json()['id']}")
        borrada = admin.delete(f"/admin/turismo/categorias/{categoria_id}")
        assert borrada.status_code == 204
