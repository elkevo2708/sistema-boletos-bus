"""Firma XAdES-BES. Sin certificado .p12 el paso se omite (desarrollo)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResultadoFirma:
    xml: str
    omitida: bool


class FirmadorOmitido:
    def firmar(self, xml: str) -> ResultadoFirma:
        return ResultadoFirma(xml=xml, omitida=True)


class FirmadorXadesBes:
    """Firma el comprobante con el .p12 configurado en el entorno."""

    def __init__(self, ruta: str, clave: str):
        self.ruta = ruta
        self.clave = clave

    def firmar(self, xml: str) -> ResultadoFirma:
        from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
        from lxml import etree
        from signxml import methods
        from signxml.xades import XAdESSigner

        archivo = Path(self.ruta)
        if not archivo.is_file():
            raise FileNotFoundError("No se encontró el certificado .p12")
        llave, certificado, _extra = load_key_and_certificates(
            archivo.read_bytes(),
            self.clave.encode("utf-8"),
        )
        if llave is None or certificado is None:
            raise ValueError("El archivo .p12 no contiene llave y certificado")
        raiz = etree.fromstring(xml.encode("utf-8"))
        firmador = XAdESSigner(method=methods.enveloped)
        firmado = firmador.sign(
            raiz,
            key=llave,
            cert=[certificado],
            reference_uri="#comprobante",
            id_attribute="id",
        )
        salida = etree.tostring(firmado, xml_declaration=True, encoding="UTF-8")
        return ResultadoFirma(xml=salida.decode("utf-8"), omitida=False)


def obtener_firmador():
    from app.config import settings

    if settings.firma_p12_ruta.strip() and settings.firma_p12_clave:
        return FirmadorXadesBes(settings.firma_p12_ruta.strip(), settings.firma_p12_clave)
    return FirmadorOmitido()
