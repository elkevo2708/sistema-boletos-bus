"""Reglas de una imagen antes de guardarla en MySQL. No necesita el servidor."""

import base64

import pytest

from app.imagenes import ImagenInvalida, normalizar_guardado, url_publica, validar_imagen

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGMQqbABAAFsAMloBcADAAAAAElFTkSuQmCC"
)
JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAACAAIDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD5XooopiP/2Q=="
)
GIF = base64.b64decode("R0lGODdhAQABAIEAABR4PAAAAAAAAAAAACwAAAAAAQABAAAIBAABBAQAOw==")
WEBP = base64.b64decode("UklGRh4AAABXRUJQVlA4TBEAAAAvAAAAAAdQvFKUp/+BiOh/AAA=")


def test_acepta_jpg_png_webp_y_gif():
    assert validar_imagen(PNG, "image/png") == "image/png"
    assert validar_imagen(JPEG, "image/jpeg") == "image/jpeg"
    assert validar_imagen(JPEG, "image/jpg") == "image/jpeg"
    assert validar_imagen(GIF, None) == "image/gif"
    assert validar_imagen(WEBP, "application/octet-stream") == "image/webp"


def test_rechaza_tipo_tamano_y_archivo_corrupto():
    with pytest.raises(ImagenInvalida, match="JPG"):
        validar_imagen(b"esto no es una imagen", "text/plain")
    with pytest.raises(ImagenInvalida, match="5 MB"):
        validar_imagen(b"", "image/png")
    with pytest.raises(ImagenInvalida, match="5 MB"):
        validar_imagen(PNG + b"\x00" * (5 * 1024 * 1024), "image/png")
    with pytest.raises(ImagenInvalida, match="no coincide"):
        validar_imagen(PNG, "image/gif")


def test_url_publica_y_guardado():
    assert url_publica("bd/4") == "/medios/bd/4"
    assert url_publica("noticia-horario.jpg") == "/medios/noticia-horario.jpg"
    assert url_publica("/turismo/panoramica.jpg") == "/turismo/panoramica.jpg"
    assert url_publica("https://cdn.ejemplo/a.jpg") == "https://cdn.ejemplo/a.jpg"
    assert normalizar_guardado("/medios/bd/4") == "bd/4"
    assert normalizar_guardado("/turismo/panoramica.jpg") == "/turismo/panoramica.jpg"
    assert normalizar_guardado("  ") is None
    with pytest.raises(ImagenInvalida):
        normalizar_guardado("javascript:alert(1)")
