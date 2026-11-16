"""Envío al SRI. En desarrollo el modo offline autoriza sin llamar a los web services."""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from xml.etree import ElementTree as ET

from app.config import settings

log = logging.getLogger("lamana.sri")

URLS = {
    "pruebas": {
        "recepcion": "https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline",
        "autorizacion": "https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline",
    },
    "produccion": {
        "recepcion": "https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline",
        "autorizacion": "https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline",
    },
}


@dataclass(frozen=True)
class ResultadoSri:
    estado: str
    numero_autorizacion: str | None
    mensaje: str
    xml_autorizado: str | None


class ClienteSriSimulado:
    async def enviar(self, xml: str, clave: str, ambiente: str) -> ResultadoSri:
        return ResultadoSri(
            estado="autorizada",
            numero_autorizacion=clave,
            mensaje="Autorizado en modo de desarrollo, sin conexión al SRI.",
            xml_autorizado=xml,
        )


class ClienteSriSoap:
    """Recepción y autorización offline del SRI. Solo se usa con SRI_MODO=en_linea."""

    async def enviar(self, xml: str, clave: str, ambiente: str) -> ResultadoSri:
        import httpx

        urls = dict(URLS.get(ambiente, URLS["pruebas"]))
        if settings.sri_recepcion_url.strip():
            urls["recepcion"] = settings.sri_recepcion_url.strip()
        if settings.sri_autorizacion_url.strip():
            urls["autorizacion"] = settings.sri_autorizacion_url.strip()
        codificado = base64.b64encode(xml.encode("utf-8")).decode("ascii")
        sobre_recepcion = _sobre(
            "http://ec.gob.sri.ws.recepcion",
            "validarComprobante",
            f"<xml>{codificado}</xml>",
        )
        async with httpx.AsyncClient(timeout=25) as cliente:
            recepcion = await cliente.post(
                urls["recepcion"],
                content=sobre_recepcion.encode("utf-8"),
                headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": '""'},
            )
            recepcion.raise_for_status()
            estado, mensajes = _estado_y_mensajes(recepcion.text)
            if estado == "DEVUELTA":
                return ResultadoSri("rechazada", None, _texto(mensajes, "El SRI devolvió el comprobante"), None)
            autorizacion = await cliente.post(
                urls["autorizacion"],
                content=_sobre(
                    "http://ec.gob.sri.ws.autorizacion",
                    "autorizacionComprobante",
                    f"<claveAccesoComprobante>{clave}</claveAccesoComprobante>",
                ).encode("utf-8"),
                headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": '""'},
            )
            autorizacion.raise_for_status()
        return _interpretar_autorizacion(autorizacion.text, xml)


def obtener_cliente_sri():
    if settings.sri_modo.strip().lower() == "en_linea":
        log.info("Facturación en línea: se usarán los web services del SRI")
        return ClienteSriSoap()
    return ClienteSriSimulado()


def _sobre(espacio: str, operacion: str, cuerpo: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
        f' xmlns:ec="{espacio}">'
        "<soapenv:Header/>"
        "<soapenv:Body>"
        f"<ec:{operacion}>{cuerpo}</ec:{operacion}>"
        "</soapenv:Body>"
        "</soapenv:Envelope>"
    )


def _locales(xml: str, nombre: str) -> list[str]:
    try:
        raiz = ET.fromstring(xml)
    except ET.ParseError:
        return []
    return [(nodo.text or "").strip() for nodo in raiz.iter() if nodo.tag.endswith(nombre) and (nodo.text or "").strip()]


def _estado_y_mensajes(xml: str) -> tuple[str, list[str]]:
    estados = _locales(xml, "estado")
    mensajes = _locales(xml, "mensaje") + _locales(xml, "informacionAdicional")
    return (estados[0] if estados else ""), mensajes


def _texto(mensajes: list[str], respaldo: str) -> str:
    limpio = "; ".join(mensajes)[:500]
    return limpio or respaldo


def _interpretar_autorizacion(xml: str, xml_firmado: str) -> ResultadoSri:
    estado, mensajes = _estado_y_mensajes(xml)
    numeros = _locales(xml, "numeroAutorizacion")
    comprobantes = _locales(xml, "comprobante")
    if estado == "AUTORIZADO":
        return ResultadoSri(
            "autorizada",
            numeros[0] if numeros else None,
            "Autorizado por el SRI",
            comprobantes[0] if comprobantes else xml_firmado,
        )
    if estado in ("EN PROCESO", "RECIBIDA", ""):
        return ResultadoSri("firmada", None, _texto(mensajes, "El SRI aún no autoriza el comprobante"), xml_firmado)
    return ResultadoSri("rechazada", None, _texto(mensajes, "El SRI rechazó el comprobante"), xml_firmado)
