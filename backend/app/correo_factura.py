"""Envío del RIDE. Sin SMTP_HOST el mensaje queda en el log (desarrollo)."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

log = logging.getLogger("lamana.correo")


def enviar_ride(destino: str | None, numero: str, clave: str, pdf: bytes) -> None:
    if not destino:
        log.info("Factura %s sin correo del comprador; no se envía", numero)
        return
    if not settings.smtp_host.strip():
        log.info(
            "Correo de factura (SMTP no configurado) para %s: factura %s, clave %s, RIDE %s bytes",
            destino,
            numero,
            clave,
            len(pdf),
        )
        return
    mensaje = EmailMessage()
    mensaje["Subject"] = f"Factura {numero} · Cooperativa de Transporte La Maná"
    mensaje["From"] = settings.smtp_desde
    mensaje["To"] = destino
    mensaje.set_content(
        "Adjuntamos el RIDE de su pasaje.\n"
        f"Factura: {numero}\n"
        f"Clave de acceso: {clave}\n"
        "Cooperativa de Transporte La Maná."
    )
    mensaje.add_attachment(pdf, maintype="application", subtype="pdf", filename=f"RIDE-{numero}.pdf")
    with smtplib.SMTP(settings.smtp_host.strip(), settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_port != 25:
            smtp.starttls()
        if settings.smtp_usuario.strip():
            smtp.login(settings.smtp_usuario.strip(), settings.smtp_clave)
        smtp.send_message(mensaje)
    log.info("RIDE enviado a %s, factura %s", destino, numero)
