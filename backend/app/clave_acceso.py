"""Clave de acceso de 49 dígitos del SRI, con dígito verificador módulo 11."""

from __future__ import annotations

from datetime import datetime


def digito_modulo11(cadena: str) -> str:
    if not cadena.isdigit():
        raise ValueError("La clave de acceso solo admite dígitos")
    factores = (2, 3, 4, 5, 6, 7)
    total = 0
    for indice, caracter in enumerate(reversed(cadena)):
        total += int(caracter) * factores[indice % 6]
    residuo = total % 11
    verificador = 11 - residuo
    if verificador == 11:
        return "0"
    if verificador == 10:
        return "1"
    return str(verificador)


def armar_clave_acceso(
    fecha: datetime,
    ruc: str,
    ambiente: str,
    establecimiento: str,
    punto_emision: str,
    secuencial: int,
    codigo_numerico: int,
) -> str:
    if len(ruc) != 13 or not ruc.isdigit():
        raise ValueError("El RUC del emisor debe tener 13 dígitos")
    if ambiente not in ("pruebas", "produccion"):
        raise ValueError("Ambiente de facturación no reconocido")
    base = (
        fecha.strftime("%d%m%Y")
        + "01"
        + ruc
        + ("1" if ambiente == "pruebas" else "2")
        + f"{int(establecimiento):03d}"
        + f"{int(punto_emision):03d}"
        + f"{int(secuencial):09d}"
        + f"{int(codigo_numerico):08d}"
        + "1"
    )
    if len(base) != 48:
        raise ValueError("La base de la clave de acceso no tiene 48 dígitos")
    return base + digito_modulo11(base)


def clave_valida(clave: str) -> bool:
    if len(clave) != 49 or not clave.isdigit():
        return False
    return digito_modulo11(clave[:48]) == clave[48]
