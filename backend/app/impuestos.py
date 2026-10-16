"""Desglose de IVA. El valor cobrado por el pasaje es el total de la factura."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

CENTAVO = Decimal("0.01")
CODIGOS_PORCENTAJE = {
    Decimal("0"): "0",
    Decimal("5"): "5",
    Decimal("12"): "2",
    Decimal("13"): "10",
    Decimal("14"): "3",
    Decimal("15"): "4",
}


def dinero(valor) -> Decimal:
    return Decimal(str(valor)).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def desglosar_iva(total, tarifa) -> tuple[Decimal, Decimal]:
    """Devuelve base imponible e IVA. El total cobrado no cambia."""
    total = dinero(total)
    tarifa = dinero(tarifa)
    if tarifa < 0 or tarifa > 100:
        raise ValueError("La tarifa de IVA debe estar entre 0 y 100")
    if tarifa == 0:
        return total, Decimal("0.00")
    base = (total / (Decimal("1") + (tarifa / Decimal("100")))).quantize(CENTAVO, rounding=ROUND_HALF_UP)
    return base, (total - base).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def codigo_porcentaje_iva(tarifa) -> str:
    tarifa = dinero(tarifa)
    if tarifa == tarifa.to_integral_value():
        codigo = CODIGOS_PORCENTAJE.get(tarifa.quantize(Decimal("1")))
        if codigo:
            return codigo
    return "8"
