"""Altas de taquilla a través del prefijo /api que publica nginx."""

import os
from datetime import date, timedelta
from secrets import token_hex

import httpx
import pytest

BASE = os.environ.get("API_BASE", "http://127.0.0.1:8080/api")
PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x00\x03\x00\x01\x00\x05\xfe\xd4\xef\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture(scope="module")
def cliente():
    with httpx.Client(base_url=BASE, timeout=30) as http:
        acceso = http.post(
            "/auth/login",
            data={"username": "admin@lamana.local", "password": "Admin123!"},
        )
        assert acceso.status_code == 200, acceso.text
        http.headers["Authorization"] = f"Bearer {acceso.json()['access_token']}"
        yield http


def test_ciudad_invalida_no_crea(cliente):
    respuesta = cliente.post("/admin/ciudades", json={"nombre": "A", "departamento": "Cotopaxi"})
    assert respuesta.status_code == 422


def test_sin_sesion_no_crea_viaje():
    respuesta = httpx.post(f"{BASE}/admin/viajes", json={"ruta_id": 1, "bus_id": 1, "salida": "2030-01-01T08:00:00"}, timeout=30)
    assert respuesta.status_code == 401


def test_flujos_de_alta(cliente):
    marca = token_hex(3).upper()
    hoy = date.today()
    fin = hoy + timedelta(days=10)
    ciudad = cliente.post(
        "/admin/ciudades",
        json={"nombre": f"Prueba {marca}", "departamento": "Cotopaxi"},
    )
    assert ciudad.status_code == 201, ciudad.text
    ciudad_id = ciudad.json()["id"]
    repetida = cliente.post(
        "/admin/ciudades",
        json={"nombre": f"Prueba {marca}", "departamento": "Cotopaxi"},
    )
    assert repetida.status_code == 409

    ciudades = cliente.get("/admin/ciudades")
    assert ciudades.status_code == 200
    otra = next(item["id"] for item in ciudades.json() if item["id"] != ciudad_id)

    ruta = cliente.post(
        "/admin/rutas",
        json={"origen_id": ciudad_id, "destino_id": otra, "duracion_min": 45, "precio_base": "4.50"},
    )
    assert ruta.status_code == 201, ruta.text
    ruta_id = ruta.json()["id"]

    misma = cliente.post(
        "/admin/rutas",
        json={"origen_id": ciudad_id, "destino_id": ciudad_id, "duracion_min": 30, "precio_base": "2.00"},
    )
    assert misma.status_code == 422

    enorme = cliente.post(
        "/admin/buses",
        json={"placa": f"X{marca}", "numero_disco": marca, "pisos": 2, "filas": 20},
    )
    assert enorme.status_code == 422

    bus = cliente.post(
        "/admin/buses",
        json={"placa": f"P{marca}", "numero_disco": f"D{marca}", "pisos": 1, "filas": 2, "estado": "operativo"},
    )
    assert bus.status_code == 201, bus.text
    cuerpo_bus = bus.json()
    assert cuerpo_bus["asientos"] == 8
    assert cuerpo_bus["capacidad"] == 8

    viaje = cliente.post(
        "/admin/viajes",
        json={"ruta_id": ruta_id, "bus_id": cuerpo_bus["id"], "salida": "2030-06-01T08:30:00"},
    )
    assert viaje.status_code == 201, viaje.text
    viaje_id = viaje.json()["id"]
    asientos = cliente.get(f"/viajes/{viaje_id}/asientos")
    assert asientos.status_code == 200, asientos.text
    puestos = asientos.json()["asientos"]
    assert len(puestos) == 8
    assert {item["tipo"] for item in puestos} == {"ventana", "pasillo"}

    tarifa_previa = next(item for item in cliente.get("/admin/rutas").json() if item["id"] == ruta_id)
    cambiada = cliente.patch(f"/admin/rutas/{ruta_id}/tarifa", json={"precio_base": "6.25"})
    assert cambiada.status_code == 200, cambiada.text
    assert cambiada.json()["precio_base"] in ("6.25", 6.25)
    restaurada = cliente.patch(
        f"/admin/rutas/{ruta_id}/tarifa",
        json={"precio_base": str(tarifa_previa["precio_base"])},
    )
    assert restaurada.status_code == 200, restaurada.text

    cancelado = cliente.delete(f"/admin/viajes/{viaje_id}")
    assert cancelado.status_code == 200, cancelado.text
    assert cancelado.json()["estado"] == "cancelado"

    post = cliente.post(
        "/admin/blog",
        json={
            "titulo": f"Nota de prueba {marca}",
            "resumen": "Resumen de la nota de prueba para taquilla.",
            "cuerpo": "Cuerpo suficientemente largo de la nota de prueba de taquilla.",
            "categoria": "noticia",
            "publicado": True,
            "publicado_en": "2030-01-02T09:00:00",
        },
    )
    assert post.status_code == 201, post.text
    assert cliente.delete(f"/admin/blog/{post.json()['id']}").status_code == 204

    texto = cliente.post(
        "/admin/anuncios",
        data={
            "titulo": f"Texto {marca}",
            "mensaje": "Mensaje de la promoción de solo texto.",
            "enlace": "/noticias",
            "texto_boton": "Leer",
            "tipo": "modal",
            "formato": "texto",
            "activo": "true",
            "inicio": hoy.isoformat(),
            "fin": fin.isoformat(),
        },
    )
    assert texto.status_code == 201, texto.text
    assert texto.json()["formato"] == "texto"

    imagen = cliente.post(
        "/admin/anuncios",
        data={
            "titulo": f"Imagen {marca}",
            "mensaje": "",
            "enlace": "",
            "texto_boton": "Ver ruta",
            "tipo": "modal",
            "formato": "imagen",
            "activo": "true",
            "inicio": hoy.isoformat(),
            "fin": fin.isoformat(),
        },
        files={"imagen": ("promo.png", PNG, "image/png")},
    )
    assert imagen.status_code == 201, imagen.text
    assert imagen.json()["imagen"].startswith("/medios/")

    pausado = cliente.patch(
        f"/admin/anuncios/{texto.json()['id']}",
        data={
            "titulo": f"Texto {marca}",
            "mensaje": "Mensaje de la promoción de solo texto.",
            "enlace": "/noticias",
            "texto_boton": "Leer",
            "tipo": "modal",
            "formato": "texto",
            "activo": "false",
            "inicio": hoy.isoformat(),
            "fin": fin.isoformat(),
        },
    )
    assert pausado.status_code == 200, pausado.text
    guardados = cliente.get("/admin/anuncios").json()
    assert next(item["activo"] for item in guardados if item["id"] == texto.json()["id"]) in (0, False)

    assert cliente.delete(f"/admin/anuncios/{texto.json()['id']}").status_code == 204
    assert cliente.delete(f"/admin/anuncios/{imagen.json()['id']}").status_code == 204

    galeria = cliente.post(
        "/admin/galeria",
        data={"titulo": f"Foto {marca}", "categoria": "buses", "descripcion": "Prueba"},
        files={"archivo": ("foto.png", PNG, "image/png")},
    )
    assert galeria.status_code == 201, galeria.text
    assert galeria.json()["url"].startswith("/medios/")
    assert cliente.delete(f"/admin/galeria/{galeria.json()['id']}").status_code == 204

    emisor = cliente.get("/admin/emisor")
    assert emisor.status_code == 200, emisor.text
    original = emisor.json()
    comercial = original["nombre_comercial"]
    tocado = cliente.put(
        "/admin/emisor",
        json={
            "ruc": original["ruc"],
            "razon_social": original["razon_social"],
            "nombre_comercial": f"{comercial} prueba",
            "establecimiento": original["establecimiento"],
            "punto_emision": original["punto_emision"],
            "direccion_matriz": original["direccion_matriz"],
            "obligado_contabilidad": bool(original["obligado_contabilidad"]),
            "ambiente": original["ambiente"],
            "tarifa_iva_pasaje": original["tarifa_iva_pasaje"],
        },
    )
    assert tocado.status_code == 200, tocado.text
    assert tocado.json()["nombre_comercial"].endswith("prueba")
    vuelto = cliente.put(
        "/admin/emisor",
        json={
            "ruc": original["ruc"],
            "razon_social": original["razon_social"],
            "nombre_comercial": comercial,
            "establecimiento": original["establecimiento"],
            "punto_emision": original["punto_emision"],
            "direccion_matriz": original["direccion_matriz"],
            "obligado_contabilidad": bool(original["obligado_contabilidad"]),
            "ambiente": original["ambiente"],
            "tarifa_iva_pasaje": original["tarifa_iva_pasaje"],
        },
    )
    assert vuelto.status_code == 200, vuelto.text

    mal_ruc = cliente.put(
        "/admin/emisor",
        json={
            "ruc": "1790012345001",
            "razon_social": original["razon_social"],
            "nombre_comercial": comercial,
            "establecimiento": original["establecimiento"],
            "punto_emision": original["punto_emision"],
            "direccion_matriz": original["direccion_matriz"],
            "obligado_contabilidad": True,
            "ambiente": "pruebas",
            "tarifa_iva_pasaje": "0",
        },
    )
    assert mal_ruc.status_code == 422

    bloqueado = cliente.delete(f"/admin/buses/{cuerpo_bus['id']}")
    assert bloqueado.status_code == 409
    assert cliente.delete(f"/admin/rutas/{ruta_id}").status_code == 409
    assert cliente.delete(f"/admin/ciudades/{ciudad_id}").status_code == 409
