"""Subida de imágenes a MySQL y lectura pública, a través de nginx."""

import base64
import os
from datetime import date, timedelta
from secrets import token_hex

import httpx
import pytest

BASE = os.environ.get("API_BASE", "http://127.0.0.1:8080/api")
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGMQqbABAAFsAMloBcADAAAAAElFTkSuQmCC"
)
GIF = base64.b64decode("R0lGODdhAQABAIEAABR4PAAAAAAAAAAAACwAAAAAAQABAAAIBAABBAQAOw==")
WEBP = base64.b64decode("UklGRh4AAABXRUJQVlA4TBEAAAAvAAAAAAdQvFKUp/+BiOh/AAA=")


def _login(http: httpx.Client, correo: str, clave: str) -> str:
    acceso = http.post("/auth/login", data={"username": correo, "password": clave})
    assert acceso.status_code == 200, acceso.text
    return acceso.json()["access_token"]


@pytest.fixture(scope="module")
def admin():
    with httpx.Client(base_url=BASE, timeout=30) as http:
        token = _login(http, "admin@lamana.local", "Admin123!")
        http.headers["Authorization"] = f"Bearer {token}"
        yield http


def test_sin_sesion_no_sube():
    respuesta = httpx.post(
        f"{BASE}/admin/imagenes",
        files={"archivo": ("foto.png", PNG, "image/png")},
        timeout=30,
    )
    assert respuesta.status_code == 401


def test_cliente_no_sube():
    marca = token_hex(4)
    with httpx.Client(base_url=BASE, timeout=30) as http:
        alta = http.post(
            "/auth/registro",
            json={
                "nombre": "Cliente",
                "apellido": "Imagen",
                "documento": f"CI{marca}",
                "email": f"cliente.imagen.{marca}@gmail.com",
                "password": "Clave1234",
            },
        )
        assert alta.status_code == 201, alta.text
        token = alta.json()["access_token"]
        subida = http.post(
            "/admin/imagenes",
            headers={"Authorization": f"Bearer {token}"},
            files={"archivo": ("foto.png", PNG, "image/png")},
        )
    assert subida.status_code == 403


def test_operador_sube_png_y_se_puede_leer(admin):
    with httpx.Client(base_url=BASE, timeout=30) as http:
        token = _login(http, "operador.turismo@lamana.local", "Operador123!")
        subida = http.post(
            "/admin/imagenes",
            headers={"Authorization": f"Bearer {token}"},
            files={"archivo": ("ficha.png", PNG, "image/png")},
        )
    assert subida.status_code == 201, subida.text
    cuerpo = subida.json()
    assert cuerpo["tipo_mime"] == "image/png"
    assert cuerpo["nombre"] == "ficha.png"
    assert cuerpo["url"].startswith("/medios/bd/")
    imagen_id = cuerpo["url"].rsplit("/", 1)[-1]
    publica = admin.get(f"/medios/bd/{imagen_id}")
    assert publica.status_code == 200, publica.text
    assert publica.headers["content-type"].startswith("image/png")
    assert publica.content == PNG
    assert admin.get("/medios/bd/999999999").status_code == 404


def test_gif_webp_y_rechazos(admin):
    gif = admin.post("/admin/imagenes", files={"archivo": ("anim.gif", GIF, "image/gif")})
    assert gif.status_code == 201, gif.text
    assert gif.json()["tipo_mime"] == "image/gif"
    webp = admin.post("/admin/imagenes", files={"archivo": ("foto.webp", WEBP, "image/webp")})
    assert webp.status_code == 201, webp.text
    assert webp.json()["tipo_mime"] == "image/webp"

    texto = admin.post("/admin/imagenes", files={"archivo": ("nota.txt", b"hola", "text/plain")})
    assert texto.status_code == 422
    assert "JPG" in texto.json()["detail"]

    vacio = admin.post("/admin/imagenes", files={"archivo": ("vacio.png", b"", "image/png")})
    assert vacio.status_code == 422
    assert "5 MB" in vacio.json()["detail"]

    grande = admin.post(
        "/admin/imagenes",
        files={"archivo": ("grande.png", b"\x00" * (5 * 1024 * 1024 + 1), "image/png")},
    )
    assert grande.status_code == 422
    assert "5 MB" in grande.json()["detail"]

    distinto = admin.post("/admin/imagenes", files={"archivo": ("mentira.gif", PNG, "image/gif")})
    assert distinto.status_code == 422
    assert "no coincide" in distinto.json()["detail"]


def test_anuncio_y_galeria_quedan_apuntando_a_la_imagen(admin):
    subida = admin.post("/admin/imagenes", files={"archivo": ("promo.png", PNG, "image/png")})
    assert subida.status_code == 201, subida.text
    url = subida.json()["url"]
    hoy = date.today()
    fin = hoy + timedelta(days=5)
    marca = token_hex(3)
    anuncio = admin.post(
        "/admin/anuncios",
        data={
            "titulo": f"Promo {marca}",
            "mensaje": "",
            "formato": "imagen",
            "tipo": "banner",
            "activo": "true",
            "inicio": hoy.isoformat(),
            "fin": fin.isoformat(),
            "imagen_url": url,
        },
    )
    assert anuncio.status_code == 201, anuncio.text
    assert anuncio.json()["imagen"] == url

    galeria = admin.post(
        "/admin/galeria",
        data={"titulo": f"Foto {marca}", "categoria": "destinos", "descripcion": "Desde el panel", "enlace": url},
    )
    assert galeria.status_code == 201, galeria.text
    assert galeria.json()["url"] == url

    javascript = admin.post(
        "/admin/galeria",
        data={"titulo": f"Mala {marca}", "categoria": "buses", "enlace": "javascript:alert(1)"},
    )
    assert javascript.status_code == 422

    assert admin.delete(f"/admin/anuncios/{anuncio.json()['id']}").status_code == 204
    assert admin.delete(f"/admin/galeria/{galeria.json()['id']}").status_code == 204
