"""Pasarelas de cobro.

Tres métodos: DeUna! (billetera Banco Pichincha), tarjeta y PayPhone.
Sin credenciales el modo es sandbox y el cobro se aprueba en esta aplicación.
Con credenciales se usan los contratos públicos:

- PayPhone botón: POST /api/button/Prepare y POST /api/button/V2/Confirm.
  Montos en centavos, clientTransactionId, moneda USD, zona -5.
  statusCode 3 y transactionStatus Approved confirman el cobro.
  https://docs.payphone.app/boton-de-pago
- Tarjeta: el mismo Prepare de PayPhone devuelve payWithCard (el PAN no pasa
  por este servidor) o, si TARJETA_API_URL está definida, un procesador propio
  que solo recibe los últimos 4 dígitos y una clave de idempotencia.
- DeUna: alta de orden en /merchants/orders (X-Api-Key, montos en centavos,
  webhook notify_order) y consulta de estado. El webhook se acepta si la firma
  HMAC coincide. https://docs.deuna.com/docs/deuna-wallet-via-widget
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

import httpx

from app.config import settings

log = logging.getLogger("lamana.pagos")

METODOS = ("deuna", "tarjeta", "payphone")
APROBADOS = {"approved", "succeeded", "processed", "authorized", "captured"}


@dataclass(frozen=True)
class SolicitudPago:
    boleto_codigo: str
    monto: Decimal
    referencia_ext: str
    metodo: str
    ultimos4: str = ""


@dataclass(frozen=True)
class InicioPago:
    aprobado: bool
    pendiente: bool
    proveedor: str
    referencia: str
    mensaje: str
    redireccion: str | None = None
    qr_texto: str | None = None
    id_externo: str | None = None


class ProveedorPago(Protocol):
    codigo: str

    async def iniciar(self, solicitud: SolicitudPago) -> InicioPago:
        """Abre el cobro. En sandbox queda aprobado; en vivo queda pendiente."""


def centavos(monto: Decimal) -> int:
    return int((Decimal(monto) * Decimal(100)).quantize(Decimal("1")))


def firmar(cuerpo: bytes, secreto: str) -> str:
    return hmac.new(secreto.encode("utf-8"), cuerpo, hashlib.sha256).hexdigest()


def firma_valida(cuerpo: bytes, recibida: str | None, secreto: str) -> bool:
    if not secreto or not recibida:
        return False
    esperada = firmar(cuerpo, secreto)
    return hmac.compare_digest(esperada, recibida.strip().lower())


def secreto_webhook() -> str:
    propio = settings.pagos_webhook_secreto.strip() or settings.deuna_api_secret.strip()
    return propio or "lamana-sandbox-firma"


def cuerpo_payphone(solicitud: SolicitudPago, response_url: str) -> dict:
    total = centavos(solicitud.monto)
    return {
        "amount": total,
        "amountWithoutTax": total,
        "amountWithTax": 0,
        "tax": 0,
        "service": 0,
        "tip": 0,
        "currency": "USD",
        "clientTransactionId": solicitud.referencia_ext[:50],
        "reference": f"Pasaje {solicitud.boleto_codigo}"[:50],
        "storeId": settings.payphone_store_id.strip(),
        "responseUrl": response_url,
        "cancellationUrl": settings.public_base_url.rstrip("/") + "/",
        "timeZone": -5,
    }


def payphone_aprobado(datos: dict, monto: Decimal) -> bool:
    estado = str(datos.get("transactionStatus") or datos.get("status") or "").strip().lower()
    codigo = datos.get("statusCode")
    if codigo not in (3, "3") and estado not in APROBADOS:
        return False
    if "amount" in datos and datos["amount"] is not None:
        return int(datos["amount"]) == centavos(monto)
    return True


def deuna_aprobado(datos: dict) -> bool:
    estado = _estado_deuna(datos)
    return estado in APROBADOS


def _estado_deuna(datos: dict) -> str:
    if not isinstance(datos, dict):
        return ""
    orden = datos.get("order") if isinstance(datos.get("order"), dict) else datos
    pago = orden.get("payment") if isinstance(orden.get("payment"), dict) else {}
    data = pago.get("data") if isinstance(pago.get("data"), dict) else {}
    bruto = data.get("status") or orden.get("status") or datos.get("status") or ""
    return str(bruto).strip().lower()


def referencia_deuna(datos: dict) -> str:
    orden = datos.get("order") if isinstance(datos.get("order"), dict) else {}
    return str(
        datos.get("clientTransactionId")
        or datos.get("order_id")
        or orden.get("order_id")
        or ""
    ).strip()


class _Sandbox:
    def __init__(self, codigo: str, mensaje: str, qr: bool = False) -> None:
        self.codigo = codigo
        self._mensaje = mensaje
        self._qr = qr

    async def iniciar(self, solicitud: SolicitudPago) -> InicioPago:
        if len(solicitud.referencia_ext.strip()) < 4:
            return InicioPago(False, False, f"sandbox:{self.codigo}", solicitud.referencia_ext, "Referencia incompleta")
        texto = f"deuna://sandbox/{solicitud.referencia_ext}" if self._qr else None
        return InicioPago(
            aprobado=True,
            pendiente=False,
            proveedor=f"sandbox:{self.codigo}",
            referencia=solicitud.referencia_ext.strip(),
            mensaje=self._mensaje,
            qr_texto=texto,
        )


class PayPhone:
    """Botón de pagos: Prepare abre la URL y Confirm cierra la transacción."""

    codigo = "payphone"

    async def iniciar(self, solicitud: SolicitudPago) -> InicioPago:
        if not _en_vivo("payphone"):
            return await _Sandbox("payphone", "Cobro de prueba aprobado. Con el token de PayPhone se abre la Cajita.").iniciar(solicitud)
        respuesta = await _post_json(
            f"{settings.payphone_api_url.rstrip('/')}/Prepare",
            cuerpo_payphone(solicitud, _url_retorno()),
            headers=_cabeceras_payphone(),
            idempotencia=solicitud.referencia_ext,
        )
        pago_id = str(respuesta.get("paymentId") or "")
        enlace = respuesta.get("payWithPayPhone") or respuesta.get("payWithCard")
        if not pago_id or not enlace:
            raise RuntimeError("PayPhone no devolvió paymentId")
        return InicioPago(
            aprobado=False,
            pendiente=True,
            proveedor="payphone",
            referencia=solicitud.referencia_ext,
            mensaje="Continue el pago en PayPhone. Hay que confirmarlo en menos de cinco minutos.",
            redireccion=str(enlace),
            id_externo=pago_id,
        )


class Tarjeta:
    """Tarjeta en la Cajita de PayPhone (payWithCard) o en un procesador configurable."""

    codigo = "tarjeta"

    async def iniciar(self, solicitud: SolicitudPago) -> InicioPago:
        if settings.tarjeta_api_url.strip() and settings.pagos_modo.strip().lower() == "live":
            return await self._procesador(solicitud)
        if _en_vivo("tarjeta"):
            respuesta = await _post_json(
                f"{settings.payphone_api_url.rstrip('/')}/Prepare",
                cuerpo_payphone(solicitud, _url_retorno()),
                headers=_cabeceras_payphone(),
                idempotencia=solicitud.referencia_ext,
            )
            enlace = respuesta.get("payWithCard")
            pago_id = str(respuesta.get("paymentId") or "")
            if not enlace or not pago_id:
                raise RuntimeError("PayPhone no devolvió el formulario de tarjeta")
            return InicioPago(
                aprobado=False,
                pendiente=True,
                proveedor="payphone:tarjeta",
                referencia=solicitud.referencia_ext,
                mensaje="El número de tarjeta lo pide PayPhone. Este servidor no lo recibe.",
                redireccion=str(enlace),
                id_externo=pago_id,
            )
        if solicitud.ultimos4 and len(solicitud.ultimos4) != 4:
            return InicioPago(False, False, "sandbox:tarjeta", solicitud.referencia_ext, "Faltan los últimos 4 dígitos")
        return await _Sandbox("tarjeta", "Cargo de prueba aprobado. El número de tarjeta no salió del navegador.").iniciar(solicitud)

    async def _procesador(self, solicitud: SolicitudPago) -> InicioPago:
        respuesta = await _post_json(
            settings.tarjeta_api_url.strip(),
            {
                "amount": centavos(solicitud.monto),
                "currency": "USD",
                "reference": solicitud.referencia_ext,
                "last4": solicitud.ultimos4,
                "description": f"Pasaje {solicitud.boleto_codigo}",
            },
            headers={
                "Authorization": f"Bearer {settings.tarjeta_api_key.strip()}",
                "Content-Type": "application/json",
            },
            idempotencia=solicitud.referencia_ext,
        )
        estado = str(respuesta.get("status") or "").lower()
        aprobado = bool(respuesta.get("approved")) or estado in APROBADOS
        return InicioPago(
            aprobado=aprobado,
            pendiente=not aprobado and estado in {"pending", "pendiente"},
            proveedor="tarjeta",
            referencia=str(respuesta.get("id") or solicitud.referencia_ext),
            mensaje=str(respuesta.get("message") or ("Cargo aprobado" if aprobado else "El procesador no aprobó el cargo")),
            id_externo=str(respuesta.get("id") or "") or None,
        )


class DeUna:
    """Orden DeUna con QR y confirmación por webhook o consulta de estado."""

    codigo = "deuna"

    async def iniciar(self, solicitud: SolicitudPago) -> InicioPago:
        if not _en_vivo("deuna"):
            return await _Sandbox(
                "deuna",
                "Cobro de prueba de DeUna!. Con DEUNA_API_KEY se genera el QR del comercio.",
                qr=True,
            ).iniciar(solicitud)
        total = centavos(solicitud.monto)
        cuerpo = {
            "order_type": "PAYMENT_LINK",
            "order": {
                "order_id": solicitud.referencia_ext[:50],
                "currency": "USD",
                "sub_total": total,
                "total_amount": total,
                "items_total_amount": total,
                "store_code": settings.deuna_point_of_sale.strip() or "all",
                "items": [
                    {
                        "id": solicitud.boleto_codigo,
                        "name": f"Pasaje {solicitud.boleto_codigo}",
                        "quantity": 1,
                        "unit_price": {"amount": total, "currency": "USD"},
                        "total_amount": {"amount": total, "currency": "USD"},
                    }
                ],
                "webhook_urls": {"notify_order": _url_webhook_deuna()},
            },
        }
        respuesta = await _post_json(
            f"{settings.deuna_api_url.rstrip('/')}/merchants/orders",
            cuerpo,
            headers={"X-Api-Key": settings.deuna_api_key.strip(), "Content-Type": "application/json"},
            idempotencia=solicitud.referencia_ext,
        )
        token = str(respuesta.get("token") or respuesta.get("order_token") or "")
        orden = respuesta.get("order") if isinstance(respuesta.get("order"), dict) else {}
        qr = respuesta.get("qr") or orden.get("qr") or (f"deuna://pay/{token}" if token else None)
        enlace = respuesta.get("payment_link") or orden.get("payment_link")
        return InicioPago(
            aprobado=False,
            pendiente=True,
            proveedor="deuna",
            referencia=solicitud.referencia_ext,
            mensaje="Escanee el QR con la app DeUna!. El webhook confirma el cobro.",
            redireccion=str(enlace) if enlace else None,
            qr_texto=str(qr) if qr else None,
            id_externo=token or None,
        )


REGISTRO: dict[str, ProveedorPago] = {
    "deuna": DeUna(),
    "tarjeta": Tarjeta(),
    "payphone": PayPhone(),
}


def obtener_proveedor(metodo: str) -> ProveedorPago | None:
    return REGISTRO.get(metodo)


def modo_de(codigo: str) -> str:
    return "live" if _en_vivo(codigo) else "sandbox"


def credenciales_de(codigo: str) -> tuple[bool, list[str]]:
    faltan: list[str] = []
    if codigo == "payphone":
        if not settings.payphone_token.strip():
            faltan.append("PAYPHONE_TOKEN")
        if not settings.payphone_store_id.strip():
            faltan.append("PAYPHONE_STORE_ID")
    elif codigo == "deuna":
        if not settings.deuna_api_key.strip():
            faltan.append("DEUNA_API_KEY")
        if not settings.deuna_api_secret.strip() and not settings.pagos_webhook_secreto.strip():
            faltan.append("DEUNA_API_SECRET")
    elif codigo == "tarjeta":
        propio = bool(settings.tarjeta_api_url.strip())
        payphone = bool(settings.payphone_token.strip())
        if settings.tarjeta_proveedor.strip().lower() == "propio" and not propio:
            faltan.append("TARJETA_API_URL")
        elif not propio and not payphone:
            faltan.extend(["PAYPHONE_TOKEN", "TARJETA_API_URL"])
    return (not faltan, faltan)


def _en_vivo(codigo: str) -> bool:
    if settings.pagos_modo.strip().lower() != "live":
        return False
    listas, _ = credenciales_de(codigo)
    if codigo == "tarjeta" and settings.tarjeta_proveedor.strip().lower() == "propio":
        return bool(settings.tarjeta_api_url.strip())
    return listas


def _cabeceras_payphone() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.payphone_token.strip()}",
        "Content-Type": "application/json",
    }


def _url_retorno() -> str:
    return settings.public_base_url.rstrip("/") + "/api/pagos/payphone/retorno"


def _url_webhook_deuna() -> str:
    return settings.public_base_url.rstrip("/") + "/api/pagos/webhooks/deuna"


async def confirmar_payphone(id_externo: str, client_tx: str) -> dict:
    return await _post_json(
        f"{settings.payphone_api_url.rstrip('/')}/V2/Confirm",
        {"id": int(id_externo) if str(id_externo).isdigit() else id_externo, "clientTxId": client_tx},
        headers=_cabeceras_payphone(),
        idempotencia=client_tx,
    )


async def consultar_deuna(order_token: str) -> dict:
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as cliente:
        respuesta = await cliente.get(
            f"{settings.deuna_api_url.rstrip('/')}/merchants/orders/{order_token}",
            headers={"X-Api-Key": settings.deuna_api_key.strip(), "Accept": "application/json"},
        )
    if respuesta.status_code >= 400:
        raise RuntimeError(f"DeUna respondió {respuesta.status_code}")
    datos = respuesta.json()
    return datos if isinstance(datos, dict) else {}


async def _post_json(url: str, cuerpo: dict, headers: dict, idempotencia: str) -> dict:
    cabeceras = dict(headers)
    cabeceras["X-Idempotency-Key"] = idempotencia[:80]
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as cliente:
        respuesta = await cliente.post(url, json=cuerpo, headers=cabeceras)
    if respuesta.status_code >= 400:
        log.warning("Pasarela %s respondió %s", url, respuesta.status_code)
        raise RuntimeError(f"La pasarela respondió {respuesta.status_code}")
    datos = respuesta.json()
    if not isinstance(datos, dict):
        raise RuntimeError("La pasarela no devolvió un objeto JSON")
    return datos
