from datetime import date, datetime
from decimal import Decimal


def limpiar(valor):
    if isinstance(valor, Decimal):
        return f"{valor:.2f}"
    if isinstance(valor, datetime):
        return valor.strftime("%Y-%m-%dT%H:%M:%S")
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, bytes):
        return valor.decode()
    return valor


def fila_a_dict(fila) -> dict:
    return {clave: limpiar(valor) for clave, valor in dict(fila).items()}
