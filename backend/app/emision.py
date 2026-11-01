"""Emite la factura en la misma transacción del pago y la completa después del commit."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.clave_acceso import armar_clave_acceso
from app.correo_factura import enviar_ride
from app.esquemas import FacturacionIn
from app.firma import obtener_firmador
from app.impuestos import desglosar_iva, dinero
from app.presentacion import fila_a_dict
from app.ride import generar_ride
from app.sri import obtener_cliente_sri
from app.tiempo import ahora_colombia
from app.xml_factura import construir_xml, forma_pago

log = logging.getLogger("lamana.facturacion")

_VIAJE = """
SELECT TRIM(b.codigo) AS codigo,
       b.precio,
       b.pasajero_nombre,
       b.pasajero_documento,
       a.numero AS asiento_numero,
       v.salida,
       co.nombre AS origen,
       cd.nombre AS destino
  FROM boletos b
  JOIN asientos a ON a.id = b.asiento_id
  JOIN viajes v ON v.id = b.viaje_id
  JOIN rutas r ON r.id = v.ruta_id
  JOIN ciudades co ON co.id = r.origen_id
  JOIN ciudades cd ON cd.id = r.destino_id
 WHERE b.id = :id
"""

_FACTURA = """
SELECT f.id, f.boleto_id, f.usuario_id, f.numero, f.clave_acceso, f.fecha_emision,
       f.ambiente, f.estado, f.subtotal, f.iva, f.total, f.firma_omitida,
       f.numero_autorizacion, f.mensaje_sri, f.email_comprador,
       f.tipo_identificacion, f.identificacion_comprador, f.razon_social_comprador,
       f.direccion_comprador, f.telefono_comprador,
       f.emisor_ruc, f.emisor_razon_social, f.emisor_nombre_comercial, f.emisor_direccion,
       f.obligado_contabilidad, f.establecimiento, f.punto_emision, f.secuencial,
       f.forma_pago, f.xml_comprobante, f.xml_autorizado,
       d.descripcion, d.tarifa_iva, d.ruta, d.salida, d.asiento, d.pasajero, d.codigo AS codigo_detalle
  FROM facturas f
  JOIN factura_detalles d ON d.factura_id = f.id
 WHERE f.id = :id
"""


async def registrar_factura(
    sesion: AsyncSession,
    boleto_id: int,
    usuario_id: int,
    comprador: FacturacionIn,
    metodo: str,
) -> int:
    emisor = (
        await sesion.execute(text("SELECT * FROM emisor WHERE id = 1 FOR UPDATE"))
    ).mappings().first()
    if emisor is None:
        raise HTTPException(status_code=500, detail="No hay emisor configurado")
    viaje = (await sesion.execute(text(_VIAJE), {"id": boleto_id})).mappings().one()
    secuencial = int(emisor["secuencial"]) + 1
    if secuencial > 999999999:
        raise HTTPException(status_code=409, detail="Se agotó el secuencial del punto de emisión")
    await sesion.execute(
        text("UPDATE emisor SET secuencial = :secuencial WHERE id = 1"),
        {"secuencial": secuencial},
    )

    fecha = ahora_colombia()
    codigo_numerico = secrets.randbelow(90_000_000) + 10_000_000
    clave = armar_clave_acceso(
        fecha,
        emisor["ruc"],
        emisor["ambiente"],
        emisor["establecimiento"],
        emisor["punto_emision"],
        secuencial,
        codigo_numerico,
    )
    total = dinero(viaje["precio"])
    tarifa = dinero(emisor["tarifa_iva_pasaje"])
    base, iva = desglosar_iva(total, tarifa)
    salida = viaje["salida"]
    salida_txt = salida.strftime("%d/%m/%Y %H:%M") if isinstance(salida, datetime) else str(salida)[:16]
    ruta = f"{viaje['origen']} - {viaje['destino']}"
    descripcion = (
        f"Pasaje {ruta}. Salida {salida_txt}. Asiento {viaje['asiento_numero']}. "
        f"Pasajero {viaje['pasajero_nombre']}."
    )[:300]
    numero = f"{int(emisor['establecimiento']):03d}-{int(emisor['punto_emision']):03d}-{secuencial:09d}"
    pago = forma_pago(metodo)
    comprobante = {
        "ambiente": emisor["ambiente"],
        "emisor_razon_social": emisor["razon_social"],
        "emisor_nombre_comercial": emisor["nombre_comercial"],
        "emisor_ruc": emisor["ruc"],
        "clave_acceso": clave,
        "establecimiento": emisor["establecimiento"],
        "punto_emision": emisor["punto_emision"],
        "secuencial": secuencial,
        "emisor_direccion": emisor["direccion_matriz"],
        "fecha_emision": fecha,
        "obligado_contabilidad": bool(emisor["obligado_contabilidad"]),
        "tipo_identificacion": comprador.tipo,
        "razon_social_comprador": comprador.razon_social,
        "identificacion_comprador": comprador.identificacion,
        "direccion_comprador": comprador.direccion,
        "email_comprador": comprador.email,
        "telefono_comprador": comprador.telefono,
        "subtotal": base,
        "total": total,
        "forma_pago": pago,
    }
    detalle = {
        "codigo": viaje["codigo"],
        "descripcion": descripcion,
        "cantidad": 1,
        "precio_unitario": base,
        "descuento": 0,
        "tarifa_iva": tarifa,
        "base_imponible": base,
        "valor_iva": iva,
        "ruta": ruta,
        "salida": salida_txt,
        "asiento": str(viaje["asiento_numero"]),
        "pasajero": viaje["pasajero_nombre"],
    }
    xml = construir_xml(comprobante, [detalle])
    resultado = await sesion.execute(
        text(
            """
            INSERT INTO facturas (
              boleto_id, usuario_id, emisor_ruc, emisor_razon_social, emisor_nombre_comercial,
              emisor_direccion, obligado_contabilidad, establecimiento, punto_emision, secuencial,
              numero, clave_acceso, fecha_emision, ambiente, tipo_identificacion,
              identificacion_comprador, razon_social_comprador, direccion_comprador,
              email_comprador, telefono_comprador, subtotal, iva, total, forma_pago,
              estado, xml_comprobante
            ) VALUES (
              :boleto_id, :usuario_id, :emisor_ruc, :emisor_razon_social, :emisor_nombre_comercial,
              :emisor_direccion, :obligado_contabilidad, :establecimiento, :punto_emision, :secuencial,
              :numero, :clave_acceso, :fecha_emision, :ambiente, :tipo_identificacion,
              :identificacion_comprador, :razon_social_comprador, :direccion_comprador,
              :email_comprador, :telefono_comprador, :subtotal, :iva, :total, :forma_pago,
              'generada', :xml_comprobante
            )
            """
        ),
        {
            "boleto_id": boleto_id,
            "usuario_id": usuario_id,
            "emisor_ruc": emisor["ruc"],
            "emisor_razon_social": emisor["razon_social"],
            "emisor_nombre_comercial": emisor["nombre_comercial"],
            "emisor_direccion": emisor["direccion_matriz"],
            "obligado_contabilidad": int(bool(emisor["obligado_contabilidad"])),
            "establecimiento": f"{int(emisor['establecimiento']):03d}",
            "punto_emision": f"{int(emisor['punto_emision']):03d}",
            "secuencial": secuencial,
            "numero": numero,
            "clave_acceso": clave,
            "fecha_emision": fecha.strftime("%Y-%m-%d %H:%M:%S"),
            "ambiente": emisor["ambiente"],
            "tipo_identificacion": comprador.tipo,
            "identificacion_comprador": comprador.identificacion,
            "razon_social_comprador": comprador.razon_social,
            "direccion_comprador": comprador.direccion,
            "email_comprador": comprador.email,
            "telefono_comprador": comprador.telefono,
            "subtotal": f"{base:.2f}",
            "iva": f"{iva:.2f}",
            "total": f"{total:.2f}",
            "forma_pago": pago,
            "xml_comprobante": xml,
        },
    )
    factura_id = resultado.lastrowid or (await sesion.execute(text("SELECT LAST_INSERT_ID()"))).scalar_one()
    await sesion.execute(
        text(
            """
            INSERT INTO factura_detalles (
              factura_id, codigo, descripcion, cantidad, precio_unitario, descuento,
              tarifa_iva, base_imponible, valor_iva, ruta, salida, asiento, pasajero
            ) VALUES (
              :factura_id, :codigo, :descripcion, 1, :precio_unitario, 0,
              :tarifa_iva, :base_imponible, :valor_iva, :ruta, :salida, :asiento, :pasajero
            )
            """
        ),
        {
            "factura_id": factura_id,
            "codigo": viaje["codigo"],
            "descripcion": descripcion,
            "precio_unitario": f"{base:.2f}",
            "tarifa_iva": f"{tarifa:.2f}",
            "base_imponible": f"{base:.2f}",
            "valor_iva": f"{iva:.2f}",
            "ruta": ruta,
            "salida": salida.strftime("%Y-%m-%d %H:%M:%S") if isinstance(salida, datetime) else salida,
            "asiento": str(viaje["asiento_numero"]),
            "pasajero": viaje["pasajero_nombre"],
        },
    )
    await sesion.execute(
        text(
            """
            INSERT INTO clientes_facturacion (identificacion, tipo, razon_social, direccion, email, telefono)
            VALUES (:identificacion, :tipo, :razon_social, :direccion, :email, :telefono)
            ON DUPLICATE KEY UPDATE
              tipo = VALUES(tipo),
              razon_social = VALUES(razon_social),
              direccion = VALUES(direccion),
              email = VALUES(email),
              telefono = VALUES(telefono)
            """
        ),
        {
            "identificacion": comprador.identificacion,
            "tipo": comprador.tipo,
            "razon_social": comprador.razon_social,
            "direccion": comprador.direccion,
            "email": comprador.email,
            "telefono": comprador.telefono,
        },
    )
    return int(factura_id)


async def completar_emision(sesion: AsyncSession, factura_id: int) -> dict:
    factura = await _leer(sesion, factura_id)
    xml = factura["xml_comprobante"]
    firma_omitida = 0
    estado = "generada"
    try:
        firmado = obtener_firmador().firmar(xml)
        xml = firmado.xml
        firma_omitida = int(firmado.omitida)
        estado = "generada" if firmado.omitida else "firmada"
    except Exception as exc:
        log.exception("No se pudo firmar la factura %s", factura_id)
        await _actualizar(sesion, factura_id, "rechazada", None, f"No se pudo firmar: {exc}"[:500], xml, 0)
        await sesion.commit()
        return await _leer(sesion, factura_id)

    try:
        resultado = await obtener_cliente_sri().enviar(xml, factura["clave_acceso"], factura["ambiente"])
        estado = resultado.estado
        numero = resultado.numero_autorizacion
        mensaje = resultado.mensaje
        xml_autorizado = resultado.xml_autorizado or xml
    except Exception as exc:
        log.exception("No se pudo enviar la factura %s al SRI", factura_id)
        estado = "rechazada"
        numero = None
        mensaje = f"No se pudo contactar al SRI: {exc}"[:500]
        xml_autorizado = xml

    await _actualizar(sesion, factura_id, estado, numero, mensaje, xml_autorizado, firma_omitida, xml_firmado=xml)
    await sesion.commit()
    factura = await _leer(sesion, factura_id)
    try:
        pdf = generar_ride(_para_ride(factura))
        enviar_ride(factura.get("email_comprador"), factura["numero"], factura["clave_acceso"], pdf)
    except Exception:
        log.exception("No se pudo enviar el RIDE de la factura %s", factura_id)
    return factura


async def reenviar(sesion: AsyncSession, factura_id: int) -> dict:
    actual = await _leer(sesion, factura_id)
    if actual["estado"] != "autorizada":
        actual = await completar_emision(sesion, factura_id)
    else:
        pdf = generar_ride(_para_ride(actual))
        enviar_ride(actual.get("email_comprador"), actual["numero"], actual["clave_acceso"], pdf)
    return actual


async def _leer(sesion: AsyncSession, factura_id: int) -> dict:
    fila = (await sesion.execute(text(_FACTURA), {"id": factura_id})).mappings().first()
    if fila is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return fila_a_dict(fila)


async def _actualizar(
    sesion: AsyncSession,
    factura_id: int,
    estado: str,
    numero: str | None,
    mensaje: str | None,
    xml_autorizado: str | None,
    firma_omitida: int,
    xml_firmado: str | None = None,
) -> None:
    await sesion.execute(
        text(
            """
            UPDATE facturas
               SET estado = :estado,
                   numero_autorizacion = :numero,
                   mensaje_sri = :mensaje,
                   xml_autorizado = :xml_autorizado,
                   xml_comprobante = COALESCE(:xml_firmado, xml_comprobante),
                   firma_omitida = :firma_omitida
             WHERE id = :id
            """
        ),
        {
            "id": factura_id,
            "estado": estado,
            "numero": numero,
            "mensaje": (mensaje or "")[:500],
            "xml_autorizado": xml_autorizado,
            "xml_firmado": xml_firmado,
            "firma_omitida": firma_omitida,
        },
    )


def resumen(factura: dict) -> dict:
    return {
        "id": factura["id"],
        "numero": factura["numero"],
        "clave_acceso": factura["clave_acceso"],
        "estado": factura["estado"],
        "fecha_emision": factura["fecha_emision"],
        "subtotal": factura["subtotal"],
        "iva": factura["iva"],
        "total": factura["total"],
        "tarifa_iva": factura.get("tarifa_iva"),
        "firma_omitida": bool(int(factura["firma_omitida"])),
        "numero_autorizacion": factura.get("numero_autorizacion"),
        "mensaje_sri": factura.get("mensaje_sri"),
        "identificacion_comprador": factura["identificacion_comprador"],
        "razon_social_comprador": factura["razon_social_comprador"],
    }


def _para_ride(factura: dict) -> dict:
    datos = dict(factura)
    datos["firma_omitida"] = bool(int(factura.get("firma_omitida") or 0))
    datos["obligado_contabilidad"] = bool(int(factura.get("obligado_contabilidad") or 0))
    return datos
