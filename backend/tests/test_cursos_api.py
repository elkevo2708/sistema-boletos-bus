"""Cursos de Aprende: catálogo, cupos y permisos."""

import os
from secrets import token_hex

import httpx
import pytest

BASE = os.environ.get("API_BASE", "http://127.0.0.1:8080/api")


def _entrar(email, password):
    acceso = httpx.post(f"{BASE}/auth/login", data={"username": email, "password": password}, timeout=30)
    assert acceso.status_code == 200, acceso.text
    return acceso.json()["access_token"]


@pytest.fixture(scope="module")
def admin():
    token = _entrar("admin@lamana.local", "Admin123!")
    with httpx.Client(base_url=BASE, timeout=30, headers={"Authorization": f"Bearer {token}"}) as http:
        yield http


def test_el_catalogo_publico_trae_ejemplos():
    respuesta = httpx.get(f"{BASE}/aprende/cursos", timeout=30)
    assert respuesta.status_code == 200, respuesta.text
    titulos = " ".join(item["titulo"] for item in respuesta.json())
    assert "Ejemplo:" in titulos
    detalle = httpx.get(f"{BASE}/aprende/cursos/ejemplo-atencion-al-visitante", timeout=30)
    assert detalle.status_code == 200, detalle.text
    assert detalle.json()["modulos"]
    assert detalle.json()["ejemplo"] is True


def test_inscripcion_controla_cupos_y_cedula(admin):
    marca = token_hex(3)
    alta = admin.post(
        "/admin/cursos",
        json={
            "titulo": f"Cupos {marca}",
            "resumen": "Curso temporal de la prueba",
            "cupos": 1,
            "gratis": True,
            "modalidad": "virtual",
        },
    )
    assert alta.status_code == 201, alta.text
    slug = alta.json()["slug"]
    cuerpo = {
        "nombre": "María Cedeño Paredes",
        "documento": "1710034065",
        "email": f"cursos.{marca}@gmail.com",
        "telefono": "0990000000",
    }
    primera = httpx.post(f"{BASE}/aprende/cursos/{slug}/inscripcion", json=cuerpo, timeout=30)
    assert primera.status_code == 201, primera.text
    repetida = httpx.post(f"{BASE}/aprende/cursos/{slug}/inscripcion", json=cuerpo, timeout=30)
    assert repetida.status_code == 409
    otra = httpx.post(
        f"{BASE}/aprende/cursos/{slug}/inscripcion",
        json={**cuerpo, "documento": "0926687856", "nombre": "José Andrade Mera", "email": f"otro.{marca}@gmail.com"},
        timeout=30,
    )
    assert otra.status_code == 409
    invalida = httpx.post(
        f"{BASE}/aprende/cursos/{slug}/inscripcion",
        json={**cuerpo, "documento": "123", "email": f"mala.{marca}@gmail.com"},
        timeout=30,
    )
    assert invalida.status_code == 422
    publico = httpx.get(f"{BASE}/aprende/cursos/{slug}", timeout=30)
    assert publico.json()["ocupados"] == 1


def test_operador_de_taxi_no_crea_cursos():
    token = _entrar("operador.taxi@lamana.local", "Operador123!")
    respuesta = httpx.post(
        f"{BASE}/admin/cursos",
        json={"titulo": "No debería crearse"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert respuesta.status_code == 403


def test_cambiar_estado_de_inscripcion(admin):
    lista = admin.get("/admin/cursos/catalogo")
    assert lista.status_code == 200
    curso = next(item for item in lista.json()["cursos"] if item["ocupados"] >= 1)
    personas = admin.get(f"/admin/cursos/{curso['id']}/inscritos")
    assert personas.status_code == 200 and personas.json()
    persona = personas.json()[0]
    cambio = admin.patch(f"/admin/cursos/inscripciones/{persona['id']}", json={"estado": "confirmado"})
    assert cambio.status_code == 200
    assert cambio.json()["estado"] == "confirmado"
    csv = admin.get(f"/admin/cursos/{curso['id']}/inscritos.csv")
    assert csv.status_code == 200
    assert "nombre,documento" in csv.text
