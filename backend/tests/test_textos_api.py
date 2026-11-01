"""Textos editables del sitio y el recorte por rol."""

import os
from secrets import token_hex

import httpx
import pytest

BASE = os.environ.get("API_BASE", "http://127.0.0.1:8080/api")


def _entrar(email, password):
    acceso = httpx.post(
        f"{BASE}/auth/login",
        data={"username": email, "password": password},
        timeout=30,
    )
    assert acceso.status_code == 200, acceso.text
    return acceso.json()["access_token"]


@pytest.fixture(scope="module")
def admin():
    token = _entrar("admin@lamana.local", "Admin123!")
    with httpx.Client(base_url=BASE, timeout=30, headers={"Authorization": f"Bearer {token}"}) as http:
        yield http


def test_el_portal_publico_trae_el_inicio():
    respuesta = httpx.get(f"{BASE}/textos", params={"espacio": "portal"}, timeout=30)
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert "portal.saber.titulo" in cuerpo
    assert "La Maná" in cuerpo["portal.saber.titulo"]


def test_espacio_desconocido_rechaza():
    respuesta = httpx.get(f"{BASE}/textos", params={"espacio": "otro"}, timeout=30)
    assert respuesta.status_code == 422


def test_sin_sesion_no_edita():
    respuesta = httpx.patch(f"{BASE}/admin/textos/1", json={"valor": "No"}, timeout=30)
    assert respuesta.status_code == 401


def test_admin_edita_y_la_web_lo_lee(admin):
    lista = admin.get("/admin/textos", params={"espacio": "taxi"})
    assert lista.status_code == 200, lista.text
    texto = next(item for item in lista.json() if item["clave"] == "taxi.titulo")
    original = texto["valor"]
    marca = f"Pide un taxi {token_hex(2)}"
    try:
        cambio = admin.patch(f"/admin/textos/{texto['id']}", json={"valor": marca})
        assert cambio.status_code == 200, cambio.text
        assert cambio.json()["valor"] == marca
        publico = httpx.get(f"{BASE}/textos", params={"espacio": "taxi"}, timeout=30)
        assert publico.json()["taxi.titulo"] == marca
        vacio = admin.patch(f"/admin/textos/{texto['id']}", json={"valor": "   "})
        assert vacio.status_code == 422
    finally:
        admin.patch(f"/admin/textos/{texto['id']}", json={"valor": original})


def test_operador_de_taxi_no_edita_el_portal():
    token = _entrar("operador.taxi@lamana.local", "Operador123!")
    lista = httpx.get(
        f"{BASE}/admin/textos",
        params={"espacio": "portal"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert lista.status_code == 403
    propios = httpx.get(
        f"{BASE}/admin/textos",
        params={"espacio": "taxi"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert propios.status_code == 200, propios.text
    assert propios.json()
    assert all(item["espacio"] == "taxi" for item in propios.json())
