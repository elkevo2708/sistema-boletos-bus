from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class SolicitudPago:
    boleto_codigo: str
    monto: Decimal
    referencia_ext: str
    metodo: str


@dataclass(frozen=True)
class ResultadoPago:
    aprobado: bool
    proveedor: str
    referencia: str
    mensaje: str


class ProveedorPago(Protocol):
    codigo: str

    def cobrar(self, solicitud: SolicitudPago) -> ResultadoPago:
        """Cobra o registra la orden. Una pasarela real reemplaza esta implementación."""


class PasarelaSimulada:
    """Adaptador de demostración. No habla con un banco: deja el contrato listo para enchufar uno."""

    def __init__(self, codigo: str, mensaje: str) -> None:
        self.codigo = codigo
        self._mensaje = mensaje

    def cobrar(self, solicitud: SolicitudPago) -> ResultadoPago:
        if len(solicitud.referencia_ext.strip()) < 4:
            return ResultadoPago(False, f"simulado:{self.codigo}", solicitud.referencia_ext, "Referencia incompleta")
        return ResultadoPago(
            aprobado=True,
            proveedor=f"simulado:{self.codigo}",
            referencia=solicitud.referencia_ext.strip(),
            mensaje=self._mensaje,
        )


REGISTRO: dict[str, ProveedorPago] = {
    "tarjeta": PasarelaSimulada("tarjeta", "Cargo simulado aprobado en la pasarela de tarjetas."),
    "transferencia": PasarelaSimulada("transferencia", "Transferencia simulada conciliada."),
    "payphone": PasarelaSimulada("payphone", "Cobro simulado por PayPhone o billetera."),
    "efectivo": PasarelaSimulada("efectivo", "Orden registrada. Presente el QR en ventanilla."),
}


def obtener_proveedor(metodo: str) -> ProveedorPago | None:
    return REGISTRO.get(metodo)
