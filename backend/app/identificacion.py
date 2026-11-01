"""Validación de identificación ecuatoriana.

Cédula: módulo 10. RUC de persona natural, sociedad privada y sociedad pública
con los coeficientes publicados por el SRI. No consulta ningún registro externo.
"""

from __future__ import annotations

import re

TIPOS = ("cedula", "ruc", "pasaporte", "consumidor_final")
CONSUMIDOR_FINAL = "9999999999999"
_PASAPORTE = re.compile(r"^[A-Za-z0-9]{5,20}$")


def _provincia_valida(digitos: str) -> bool:
    provincia = int(digitos[:2])
    return 1 <= provincia <= 24 or provincia == 30


def _modulo10(nueve: str) -> int:
    coeficientes = (2, 1, 2, 1, 2, 1, 2, 1, 2)
    total = 0
    for indice, coeficiente in enumerate(coeficientes):
        producto = int(nueve[indice]) * coeficiente
        if producto >= 10:
            producto -= 9
        total += producto
    return (10 - (total % 10)) % 10


def _modulo11(digitos: str, coeficientes: tuple[int, ...]) -> int | None:
    total = sum(int(digitos[indice]) * coeficiente for indice, coeficiente in enumerate(coeficientes))
    residuo = total % 11
    verificador = 0 if residuo == 0 else 11 - residuo
    if verificador == 10:
        return None
    return verificador


def cedula_valida(numero: str) -> bool:
    if len(numero) != 10 or not numero.isdigit():
        return False
    if not _provincia_valida(numero):
        return False
    if int(numero[2]) > 5:
        return False
    return _modulo10(numero[:9]) == int(numero[9])


def _ruc_natural(numero: str) -> bool:
    return cedula_valida(numero[:10]) and numero[10:] != "000"


def _ruc_privado(numero: str) -> bool:
    if int(numero[2]) != 9 or numero[10:] == "000":
        return False
    verificador = _modulo11(numero[:9], (4, 3, 2, 7, 6, 5, 4, 3, 2))
    return verificador is not None and verificador == int(numero[9])


def _ruc_publico(numero: str) -> bool:
    if int(numero[2]) != 6 or numero[9:] == "0000":
        return False
    verificador = _modulo11(numero[:8], (3, 2, 7, 6, 5, 4, 3, 2))
    return verificador is not None and verificador == int(numero[8])


def ruc_valido(numero: str) -> bool:
    if len(numero) != 13 or not numero.isdigit() or not _provincia_valida(numero):
        return False
    tercer = int(numero[2])
    if tercer < 6:
        return _ruc_natural(numero)
    if tercer == 6:
        return _ruc_publico(numero)
    if tercer == 9:
        return _ruc_privado(numero)
    return False


def clasificar_ruc(numero: str) -> str | None:
    if not ruc_valido(numero):
        return None
    tercer = int(numero[2])
    if tercer < 6:
        return "natural"
    if tercer == 6:
        return "publico"
    return "privado"


def validar_identificacion(tipo: str, identificacion: str) -> str | None:
    """Devuelve un mensaje de error, o None si la identificación es válida."""
    numero = (identificacion or "").strip().upper()
    if tipo not in TIPOS:
        return "Tipo de identificación no reconocido"
    if tipo == "consumidor_final":
        if numero != CONSUMIDOR_FINAL:
            return "El consumidor final usa la identificación 9999999999999"
        return None
    if tipo == "pasaporte":
        if _PASAPORTE.fullmatch(numero) is None:
            return "El pasaporte debe tener entre 5 y 20 letras o números"
        return None
    if tipo == "cedula":
        if not cedula_valida(numero):
            return "La cédula no supera el dígito verificador módulo 10"
        return None
    if not ruc_valido(numero):
        return "El RUC no corresponde a persona natural, sociedad privada ni sociedad pública"
    return None
