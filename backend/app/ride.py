"""RIDE en PDF: logo, clave de acceso, comprador, pasaje y totales."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path

from reportlab.graphics.barcode import code128
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

LOGO = Path(__file__).resolve().parent.parent / "recursos" / "logo-lamana.png"


def generar_ride(factura: dict) -> bytes:
    buffer = BytesIO()
    pagina = canvas.Canvas(buffer, pagesize=A4)
    ancho, alto = A4
    y = alto - 36

    if LOGO.is_file():
        pagina.drawImage(
            ImageReader(str(LOGO)),
            36,
            alto - 108,
            width=150,
            height=78,
            preserveAspectRatio=True,
            mask="auto",
            anchor="sw",
        )
    pagina.setFillColorRGB(0, 0.42, 0)
    pagina.setFont("Helvetica-Bold", 11)
    pagina.drawRightString(ancho - 36, alto - 48, _win(factura["emisor_razon_social"]))
    pagina.setFillColorRGB(0.1, 0.1, 0.1)
    pagina.setFont("Helvetica", 9)
    pagina.drawRightString(ancho - 36, alto - 62, f"RUC {factura['emisor_ruc']}")
    pagina.drawRightString(ancho - 36, alto - 74, _win(factura["emisor_direccion"]))
    pagina.setFont("Helvetica-Bold", 12)
    pagina.drawRightString(ancho - 36, alto - 92, f"FACTURA {factura['numero']}")
    ambiente = "PRUEBAS" if factura["ambiente"] == "pruebas" else "PRODUCCIÓN"
    pagina.setFont("Helvetica", 8)
    pagina.drawRightString(ancho - 36, alto - 104, f"Ambiente {ambiente}")

    y = alto - 128
    pagina.setFont("Helvetica-Bold", 8)
    pagina.drawString(36, y, "CLAVE DE ACCESO")
    y -= 46
    _dibujar_codigo(pagina, str(factura["clave_acceso"]), 36, y, ancho - 72)
    y -= 14
    pagina.setFont("Helvetica", 7.5)
    pagina.drawString(36, y, str(factura["clave_acceso"]))
    if factura.get("numero_autorizacion"):
        y -= 12
        pagina.drawString(36, y, f"Nro. autorización {factura['numero_autorizacion']}")

    y -= 22
    mitad = ancho / 2
    y = _caja(pagina, 36, y, mitad - 44, "Emisor", [
        factura["emisor_razon_social"],
        f"RUC {factura['emisor_ruc']}",
        factura["emisor_direccion"],
        "Obligado a llevar contabilidad: " + ("SI" if factura["obligado_contabilidad"] else "NO"),
    ])
    y_comprador = _caja(pagina, mitad + 8, y + _alto_caja(4), mitad - 44, "Comprador", [
        factura["razon_social_comprador"],
        f"{_etiqueta_tipo(factura['tipo_identificacion'])} {factura['identificacion_comprador']}",
        factura["direccion_comprador"],
        factura.get("email_comprador") or "",
    ])
    y = min(y, y_comprador) - 16

    pagina.setFillColorRGB(0, 0.42, 0)
    pagina.rect(36, y - 4, ancho - 72, 16, fill=1, stroke=0)
    pagina.setFillColorRGB(1, 1, 1)
    pagina.setFont("Helvetica-Bold", 8)
    pagina.drawString(42, y, "Descripción")
    pagina.drawRightString(ancho - 42, y, "Total")
    y -= 22
    pagina.setFillColorRGB(0.1, 0.1, 0.1)
    pagina.setFont("Helvetica", 9)
    descripcion = factura.get("descripcion") or "Pasaje de transporte terrestre de pasajeros"
    pagina.drawString(42, y, _win(descripcion)[:90])
    pagina.drawRightString(ancho - 42, y, f"USD {_monto(factura['total'])}")

    y -= 28
    pagina.setStrokeColorRGB(0, 0.42, 0)
    pagina.setLineWidth(1)
    pagina.roundRect(36, y - 62, ancho - 72, 74, 4, fill=0, stroke=1)
    pagina.setFont("Helvetica-Bold", 9)
    pagina.drawString(46, y, "Detalle del pasaje")
    pagina.setFont("Helvetica", 9)
    pagina.drawString(46, y - 16, _win(f"Ruta: {factura.get('ruta') or ''}"))
    pagina.drawString(46, y - 30, f"Salida: {_fecha(factura.get('salida'))}")
    pagina.drawString(46, y - 44, _win(f"Asiento: {factura.get('asiento') or ''}    Pasajero: {factura.get('pasajero') or ''}"))
    y -= 86

    pagina.setFont("Helvetica", 9)
    pagina.drawRightString(ancho - 120, y, "Subtotal 0% / base")
    pagina.drawRightString(ancho - 42, y, f"USD {_monto(factura['subtotal'])}")
    y -= 14
    pagina.drawRightString(ancho - 120, y, f"IVA {_monto(factura.get('tarifa_iva', 0))}%")
    pagina.drawRightString(ancho - 42, y, f"USD {_monto(factura['iva'])}")
    y -= 16
    pagina.setFont("Helvetica-Bold", 11)
    pagina.setFillColorRGB(0.84, 0.30, 0.06)
    pagina.drawRightString(ancho - 120, y, "Total")
    pagina.drawRightString(ancho - 42, y, f"USD {_monto(factura['total'])}")

    pagina.setFillColorRGB(0.2, 0.25, 0.2)
    pagina.setFont("Helvetica", 7.5)
    nota = factura.get("mensaje_sri") or ""
    if factura.get("firma_omitida"):
        nota = (nota + " Firma electrónica omitida: no hay certificado .p12.").strip()
    pagina.drawString(36, 40, _win(nota)[:140])
    pagina.drawString(36, 28, "Cooperativa de Transporte La Maná · transporte terrestre de pasajeros")
    pagina.showPage()
    pagina.save()
    return buffer.getvalue()


def _dibujar_codigo(pagina: canvas.Canvas, clave: str, x: float, y: float, ancho: float) -> None:
    barra = code128.Code128(clave, barHeight=34, barWidth=1, humanReadable=False)
    escala = min(1, ancho / float(barra.width))
    pagina.saveState()
    pagina.translate(x, y)
    pagina.scale(escala, 1)
    barra.drawOn(pagina, 0, 0)
    pagina.restoreState()


def _caja(pagina, x, y, ancho, titulo, lineas) -> float:
    utiles = [linea for linea in lineas if linea]
    alto = 18 + 12 * len(utiles)
    pagina.setStrokeColorRGB(0.75, 0.75, 0.75)
    pagina.setLineWidth(0.6)
    pagina.roundRect(x, y - alto, ancho, alto, 3, fill=0, stroke=1)
    pagina.setFillColorRGB(0, 0.42, 0)
    pagina.setFont("Helvetica-Bold", 8)
    pagina.drawString(x + 8, y - 14, titulo.upper())
    pagina.setFillColorRGB(0.1, 0.1, 0.1)
    pagina.setFont("Helvetica", 8)
    cursor = y - 28
    for linea in utiles:
        pagina.drawString(x + 8, cursor, _win(linea)[:58])
        cursor -= 12
    return y - alto


def _alto_caja(lineas: int) -> float:
    return 18 + 12 * lineas


def _etiqueta_tipo(tipo: str) -> str:
    return {
        "cedula": "Cédula",
        "ruc": "RUC",
        "pasaporte": "Pasaporte",
        "consumidor_final": "Consumidor final",
    }.get(tipo, "Identificación")


def _monto(valor) -> str:
    return f"{valor:.2f}" if not isinstance(valor, str) else f"{float(valor):.2f}"


def _fecha(valor) -> str:
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    if not valor:
        return ""
    texto = str(valor).replace("T", " ")
    if len(texto) >= 16 and texto[4] == "-":
        return f"{texto[8:10]}/{texto[5:7]}/{texto[0:4]} {texto[11:16]}"
    return texto[:16]


def _win(texto: str) -> str:
    return (texto or "").encode("latin-1", "replace").decode("latin-1")
