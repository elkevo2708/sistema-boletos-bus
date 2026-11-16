"""Imágenes del panel guardadas en MySQL y servidas por el backend."""

import io
import re
from pathlib import Path

from PIL import Image
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

TOPE = 5 * 1024 * 1024
PREFIJO = "bd/"
MIME_PERMITIDOS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
ALIASES = {"image/jpg": "image/jpeg", "image/pjpeg": "image/jpeg", "image/x-png": "image/png"}
_FIRMAS = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
)


class ImagenInvalida(ValueError):
    """El archivo o la URL no sirven como imagen del sitio."""


def url_publica(valor: str | None) -> str | None:
    """Convierte lo guardado en la columna en una ruta que el navegador puede pedir."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    if texto.startswith(("http://", "https://", "/")):
        return texto
    return f"/medios/{texto}"


def normalizar_guardado(valor: str | None, maximo: int = 500) -> str | None:
    """Deja `bd/{id}` o una URL absoluta. Rechaza esquemas que no son una imagen."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    if texto.startswith("/medios/"):
        texto = texto[len("/medios/") :]
    if len(texto) > maximo:
        raise ImagenInvalida("La URL de la imagen es demasiado larga")
    if texto.startswith(("http://", "https://")):
        return texto
    if texto.startswith("/") and not texto.startswith("//"):
        return texto
    if "://" in texto or texto.startswith("//") or ".." in texto.split("/"):
        raise ImagenInvalida("La URL de la imagen no es válida")
    if not re.fullmatch(r"[A-Za-z0-9._/\-]+", texto):
        raise ImagenInvalida("La URL de la imagen no es válida")
    return texto


def _mime_por_firma(contenido: bytes) -> str | None:
    for firma, mime in _FIRMAS:
        if contenido.startswith(firma):
            return mime
    if len(contenido) >= 12 and contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        return "image/webp"
    return None


def validar_imagen(contenido: bytes, tipo_declarado: str | None) -> str:
    if not contenido or len(contenido) > TOPE:
        raise ImagenInvalida("La imagen debe pesar entre 1 byte y 5 MB")
    mime = _mime_por_firma(contenido)
    if mime is None:
        raise ImagenInvalida("Solo se aceptan imágenes JPG, PNG, WebP o GIF")
    declarado = ALIASES.get((tipo_declarado or "").split(";")[0].strip().lower(), (tipo_declarado or "").split(";")[0].strip().lower())
    if declarado in MIME_PERMITIDOS and declarado != mime:
        raise ImagenInvalida("El archivo no coincide con el tipo indicado")
    try:
        with Image.open(io.BytesIO(contenido)) as imagen:
            imagen.load()
            if imagen.width < 1 or imagen.height < 1:
                raise ImagenInvalida("El archivo no es una imagen válida")
    except ImagenInvalida:
        raise
    except Exception as exc:
        raise ImagenInvalida("El archivo no es una imagen válida") from exc
    return mime


def nombre_seguro(nombre: str | None, mime: str) -> str:
    base = Path(nombre or "").name
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", base).strip(".-")[:180]
    if not base or base.startswith("."):
        return f"imagen{MIME_PERMITIDOS[mime]}"
    return base


_INSERT = text(
    """
    INSERT INTO imagenes (nombre, tipo_mime, tamano, contenido)
    VALUES (:nombre, :tipo_mime, :tamano, UNHEX(:contenido_hex))
    """
)


async def insertar_imagen(sesion: AsyncSession, nombre: str | None, mime: str, contenido: bytes) -> dict:
    seguro = nombre_seguro(nombre, mime)
    # El binario va en hexadecimal: aiomysql 0.2 no escapa bytes con el PyMySQL actual.
    resultado = await sesion.execute(
        _INSERT,
        {
            "nombre": seguro,
            "tipo_mime": mime,
            "tamano": len(contenido),
            "contenido_hex": contenido.hex(),
        },
    )
    imagen_id = int(resultado.lastrowid)
    return {
        "id": imagen_id,
        "nombre": seguro,
        "tipo_mime": mime,
        "tamano": len(contenido),
        "ruta": f"{PREFIJO}{imagen_id}",
        "url": f"/medios/{PREFIJO}{imagen_id}",
    }


async def leer_imagen(sesion: AsyncSession, imagen_id: int) -> dict | None:
    fila = (
        await sesion.execute(
            text("SELECT id, nombre, tipo_mime, tamano, contenido FROM imagenes WHERE id = :id"),
            {"id": imagen_id},
        )
    ).mappings().first()
    if fila is None:
        return None
    datos = dict(fila)
    crudo = datos["contenido"]
    if isinstance(crudo, memoryview):
        datos["contenido"] = crudo.tobytes()
    else:
        datos["contenido"] = bytes(crudo)
    return datos
