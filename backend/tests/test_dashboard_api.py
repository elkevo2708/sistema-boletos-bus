"""Resumen agregado del panel, con el recorte de cada rol."""

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


def test_resumen_exige_sesion():
    respuesta = httpx.get(f"{BASE}/admin/dashboard/resumen", timeout=30)
    assert respuesta.status_code == 401


def test_cliente_no_ve_el_panel():
    marca = token_hex(3)
    alta = httpx.post(
        f"{BASE}/auth/registro",
        json={
            "nombre": "Nuria",
            "apellido": "Prueba",
            "documento": f"8{marca}",
            "email": f"panel.{marca}@gmail.com",
            "password": "ClaveSegura1",
        },
        timeout=30,
    )
    assert alta.status_code == 201, alta.text
    respuesta = httpx.get(
        f"{BASE}/admin/dashboard/resumen",
        headers={"Authorization": f"Bearer {alta.json()['access_token']}"},
        timeout=30,
    )
    assert respuesta.status_code == 403


def test_admin_recibe_los_tres_modulos(admin):
    respuesta = admin.get("/admin/dashboard/resumen", params={"desde": "2026-10-01", "hasta": "2026-10-29"})
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["rol"] == "administrador"
    assert cuerpo["desde"] == "2026-10-01"
    assert cuerpo["hasta"] == "2026-10-29"
    assert len(cuerpo["transporte"]["ventas_por_dia"]) == 29
    assert {item["fecha"] for item in cuerpo["transporte"]["ventas_por_dia"][:1]} == {"2026-10-01"}
    kpis = cuerpo["transporte"]["kpis"]
    assert {"ventas_hoy", "ventas_mes", "boletos", "viajes_activos", "ocupacion"} <= set(kpis)
    assert "variacion" in kpis["ventas_hoy"]
    assert len(cuerpo["taxi"]["por_hora"]) == 24
    assert cuerpo["taxi"]["por_hora"][0]["hora"] == 0
    assert cuerpo["turismo"]["top_atractivos"]
    assert cuerpo["turismo"]["atractivos"] >= 1
    assert "fichas" in cuerpo["turismo"]
    assert isinstance(cuerpo["avisos"], list) and cuerpo["avisos"]


def test_rango_invertido_rechaza(admin):
    respuesta = admin.get("/admin/dashboard/resumen", params={"desde": "2026-10-20", "hasta": "2026-10-01"})
    assert respuesta.status_code == 422


def test_rango_demasiado_largo_rechaza(admin):
    respuesta = admin.get("/admin/dashboard/resumen", params={"desde": "2020-01-01", "hasta": "2026-01-01"})
    assert respuesta.status_code == 422


def test_operador_transporte_solo_ve_boletos():
    token = _entrar("operador.transporte@lamana.local", "Operador123!")
    respuesta = httpx.get(
        f"{BASE}/admin/dashboard/resumen",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert "transporte" in cuerpo
    assert "turismo" not in cuerpo
    assert "taxi" not in cuerpo


def test_operador_turismo_solo_ve_el_portal():
    token = _entrar("operador.turismo@lamana.local", "Operador123!")
    respuesta = httpx.get(
        f"{BASE}/admin/dashboard/resumen",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert "turismo" in cuerpo
    assert cuerpo["turismo"]["eventos_publicados"] >= 1
    assert "transporte" not in cuerpo
    assert "taxi" not in cuerpo


def test_operador_taxi_solo_ve_unidades():
    token = _entrar("operador.taxi@lamana.local", "Operador123!")
    respuesta = httpx.get(
        f"{BASE}/admin/dashboard/resumen",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert "taxi" in cuerpo
    assert "unidades" in cuerpo["taxi"]
    assert "kpis" in cuerpo["taxi"]
    assert "transporte" not in cuerpo
    assert "turismo" not in cuerpo
