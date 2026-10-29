import re
import unicodedata


def slugificar(texto: str) -> str:
    normal = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^a-z0-9]+", "-", normal.lower()).strip("-")
    return (base or "nota")[:140]
