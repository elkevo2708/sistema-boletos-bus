"""Comprobante XML de factura electrónica, versión 1.1.0 del SRI."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from xml.etree import ElementTree as ET

from app.impuestos import codigo_porcentaje_iva, dinero

TIPOS_COMPRADOR = {
    "ruc": "04",
    "cedula": "05",
    "pasaporte": "06",
    "consumidor_final": "07",
}
FORMAS_PAGO = {
    "tarjeta": "19",
    "transferencia": "20",
    "payphone": "20",
    "efectivo": "01",
}


def forma_pago(metodo: str) -> str:
    try:
        return FORMAS_PAGO[metodo]
    except KeyError as exc:
        raise ValueError("Método de pago sin forma de pago del SRI") from exc


def _nodo(padre: ET.Element, etiqueta: str, valor) -> ET.Element:
    nodo = ET.SubElement(padre, etiqueta)
    nodo.text = str(valor)
    return nodo


def _monto(valor) -> str:
    return f"{dinero(valor):.2f}"


def construir_xml(comprobante: dict, detalles: list[dict]) -> str:
    if not detalles:
        raise ValueError("La factura necesita al menos un detalle")
    factura = ET.Element("factura", {"id": "comprobante", "version": "1.1.0"})
    tributaria = ET.SubElement(factura, "infoTributaria")
    ambiente = comprobante["ambiente"]
    _nodo(tributaria, "ambiente", "1" if ambiente == "pruebas" else "2")
    _nodo(tributaria, "tipoEmision", "1")
    _nodo(tributaria, "razonSocial", comprobante["emisor_razon_social"])
    _nodo(tributaria, "nombreComercial", comprobante["emisor_nombre_comercial"])
    _nodo(tributaria, "ruc", comprobante["emisor_ruc"])
    _nodo(tributaria, "claveAcceso", comprobante["clave_acceso"])
    _nodo(tributaria, "codDoc", "01")
    _nodo(tributaria, "estab", f"{int(comprobante['establecimiento']):03d}")
    _nodo(tributaria, "ptoEmi", f"{int(comprobante['punto_emision']):03d}")
    _nodo(tributaria, "secuencial", f"{int(comprobante['secuencial']):09d}")
    _nodo(tributaria, "dirMatriz", comprobante["emisor_direccion"])

    info = ET.SubElement(factura, "infoFactura")
    fecha: datetime = comprobante["fecha_emision"]
    _nodo(info, "fechaEmision", fecha.strftime("%d/%m/%Y"))
    _nodo(info, "dirEstablecimiento", comprobante["emisor_direccion"])
    _nodo(info, "obligadoContabilidad", "SI" if comprobante["obligado_contabilidad"] else "NO")
    _nodo(info, "tipoIdentificacionComprador", TIPOS_COMPRADOR[comprobante["tipo_identificacion"]])
    _nodo(info, "razonSocialComprador", comprobante["razon_social_comprador"])
    _nodo(info, "identificacionComprador", comprobante["identificacion_comprador"])
    _nodo(info, "direccionComprador", comprobante["direccion_comprador"])
    _nodo(info, "totalSinImpuestos", _monto(comprobante["subtotal"]))
    _nodo(info, "totalDescuento", "0.00")

    totales = ET.SubElement(info, "totalConImpuestos")
    grupos: dict[tuple[str, str], list] = {}
    for detalle in detalles:
        tarifa = dinero(detalle["tarifa_iva"])
        clave = (codigo_porcentaje_iva(tarifa), f"{tarifa:.2f}")
        grupos.setdefault(clave, [Decimal("0.00"), Decimal("0.00")])
        grupos[clave][0] += dinero(detalle["base_imponible"])
        grupos[clave][1] += dinero(detalle["valor_iva"])
    for (codigo, tarifa), (base, valor) in grupos.items():
        impuesto = ET.SubElement(totales, "totalImpuesto")
        _nodo(impuesto, "codigo", "2")
        _nodo(impuesto, "codigoPorcentaje", codigo)
        _nodo(impuesto, "baseImponible", _monto(base))
        _nodo(impuesto, "valor", _monto(valor))

    _nodo(info, "propina", "0.00")
    _nodo(info, "importeTotal", _monto(comprobante["total"]))
    _nodo(info, "moneda", "DOLAR")
    pagos = ET.SubElement(info, "pagos")
    pago = ET.SubElement(pagos, "pago")
    _nodo(pago, "formaPago", comprobante["forma_pago"])
    _nodo(pago, "total", _monto(comprobante["total"]))

    nodo_detalles = ET.SubElement(factura, "detalles")
    for detalle in detalles:
        nodo = ET.SubElement(nodo_detalles, "detalle")
        _nodo(nodo, "codigoPrincipal", detalle["codigo"])
        _nodo(nodo, "descripcion", detalle["descripcion"])
        _nodo(nodo, "cantidad", _monto(detalle["cantidad"]))
        _nodo(nodo, "precioUnitario", _monto(detalle["precio_unitario"]))
        _nodo(nodo, "descuento", _monto(detalle.get("descuento", 0)))
        _nodo(nodo, "precioTotalSinImpuesto", _monto(detalle["base_imponible"]))
        impuestos = ET.SubElement(nodo, "impuestos")
        impuesto = ET.SubElement(impuestos, "impuesto")
        tarifa = dinero(detalle["tarifa_iva"])
        _nodo(impuesto, "codigo", "2")
        _nodo(impuesto, "codigoPorcentaje", codigo_porcentaje_iva(tarifa))
        _nodo(impuesto, "tarifa", f"{tarifa:.2f}")
        _nodo(impuesto, "baseImponible", _monto(detalle["base_imponible"]))
        _nodo(impuesto, "valor", _monto(detalle["valor_iva"]))

    adicional = ET.SubElement(factura, "infoAdicional")
    campos = [
        ("Email", comprobante.get("email_comprador")),
        ("Telefono", comprobante.get("telefono_comprador")),
        ("Ruta", detalles[0].get("ruta")),
        ("Salida", _salida(detalles[0].get("salida"))),
        ("Asiento", detalles[0].get("asiento")),
        ("Pasajero", detalles[0].get("pasajero")),
    ]
    for nombre, valor in campos:
        if valor:
            campo = ET.SubElement(adicional, "campoAdicional", {"nombre": nombre})
            campo.text = str(valor)

    return ET.tostring(factura, encoding="UTF-8", xml_declaration=True).decode("UTF-8")


def _salida(valor) -> str:
    if valor is None or valor == "":
        return ""
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    texto = str(valor).replace("T", " ")
    return texto[:16]
