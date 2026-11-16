import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.cobro import guardar_intencion, metodo_habilitado, registrar_cobro
from app.dependencias import obtener_sesion, usuario_actual
from app.emision import _leer, completar_emision, resumen
from app.errores import CodigoDuplicado, traducir_error_mysql
from app.esquemas import PagarIn, ReservarIn
from app.pagos import SolicitudPago, obtener_proveedor
from app.presentacion import fila_a_dict
from app.qr import png_base64
from app.ws import publicar_asiento

log = logging.getLogger("lamana.boletos")

router = APIRouter()

_INSERT_BOLETO = """
INSERT INTO boletos (
  codigo, viaje_id, asiento_id, usuario_id,
  pasajero_nombre, pasajero_documento, precio, estado, reservado_hasta
)
SELECT :codigo,
       v.id,
       :asiento_id,
       :usuario_id,
       :pasajero_nombre,
       :pasajero_documento,
       v.precio,
       'reservado',
       DATE_ADD(NOW(), INTERVAL 10 MINUTE)
  FROM viajes v
 WHERE v.id = :viaje_id
"""

_SELECT_BOLETO = """
SELECT TRIM(b.codigo) AS codigo,
       b.viaje_id,
       b.asiento_id,
       b.estado,
       b.precio,
       b.reservado_hasta,
       b.pasajero_nombre,
       b.pasajero_documento,
       a.numero AS asiento_numero
  FROM boletos b
  JOIN asientos a ON a.id = b.asiento_id
 WHERE b.codigo = :codigo
"""


async def _leer_boleto(sesion: AsyncSession, codigo: str) -> dict | None:
    fila = (
        await sesion.execute(text(_SELECT_BOLETO), {"codigo": codigo})
    ).mappings().first()
    return fila_a_dict(fila) if fila else None


@router.post("/reservar", status_code=201)
async def reservar(
    datos: ReservarIn,
    usuario: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    codigo = ""
    for _ in range(5):
        codigo = secrets.token_hex(6).upper()
        try:
            await sesion.execute(
                text(_INSERT_BOLETO),
                {
                    "codigo": codigo,
                    "viaje_id": datos.viaje_id,
                    "asiento_id": datos.asiento_id,
                    "usuario_id": usuario["id"],
                    "pasajero_nombre": datos.pasajero_nombre,
                    "pasajero_documento": datos.pasajero_documento,
                },
            )
            creado = (
                await sesion.execute(
                    text("SELECT id FROM boletos WHERE codigo = :codigo"),
                    {"codigo": codigo},
                )
            ).first()
            if creado is None:
                await sesion.rollback()
                raise HTTPException(status_code=404, detail="Viaje no encontrado")
            await sesion.commit()
            break
        except HTTPException:
            raise
        except SQLAlchemyError as exc:
            await sesion.rollback()
            try:
                traducir_error_mysql(exc)
            except CodigoDuplicado:
                continue
    else:
        raise HTTPException(status_code=503, detail="No se pudo generar el código del boleto")

    boleto = await _leer_boleto(sesion, codigo)
    if boleto is None:
        raise HTTPException(status_code=500, detail="La reserva no quedó registrada")
    await publicar_asiento(sesion, boleto["viaje_id"], boleto["asiento_id"])
    return boleto


@router.post("/{codigo}/pagar")
async def pagar(
    codigo: str,
    datos: PagarIn,
    usuario: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    codigo = codigo.strip().upper()
    try:
        bloqueado = (
            await sesion.execute(
                text(
                    """
                    SELECT id, estado, usuario_id, viaje_id, asiento_id, precio,
                           pasajero_nombre, pasajero_documento,
                           (reservado_hasta < NOW()) AS vencida
                      FROM boletos
                     WHERE codigo = :codigo
                     FOR UPDATE
                    """
                ),
                {"codigo": codigo},
            )
        ).mappings().first()
        if bloqueado is None:
            raise HTTPException(status_code=404, detail="Boleto no encontrado")
        if bloqueado["usuario_id"] != usuario["id"] and usuario["rol"] != "administrador":
            raise HTTPException(status_code=403, detail="No puede pagar este boleto")
        if bloqueado["estado"] != "reservado":
            raise HTTPException(status_code=409, detail="El boleto no está reservado")
        if bloqueado["vencida"]:
            raise HTTPException(status_code=409, detail="La reserva expiró")

        if not await metodo_habilitado(sesion, datos.metodo):
            raise HTTPException(status_code=422, detail="Ese método de pago está desactivado")
        proveedor = obtener_proveedor(datos.metodo)
        if proveedor is None:
            raise HTTPException(status_code=422, detail="Método de pago no disponible")
        try:
            cobro = await proveedor.iniciar(
                SolicitudPago(
                    boleto_codigo=codigo,
                    monto=bloqueado["precio"],
                    referencia_ext=datos.referencia_ext,
                    metodo=datos.metodo,
                    ultimos4=(datos.ultimos4 or "").strip(),
                )
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail="La pasarela no pudo abrir el cobro") from exc
        if cobro.pendiente:
            await guardar_intencion(
                sesion,
                boleto_id=int(bloqueado["id"]),
                usuario_id=int(usuario["id"]),
                metodo=datos.metodo,
                client_tx_id=datos.referencia_ext,
                id_externo=cobro.id_externo,
                monto=bloqueado["precio"],
                proveedor=cobro.proveedor,
                facturacion=datos.facturacion,
            )
            await sesion.commit()
            return {
                "estado": "pendiente",
                "codigo": codigo,
                "redireccion": cobro.redireccion,
                "qr_texto": cobro.qr_texto,
                "id_externo": cobro.id_externo,
                "mensaje": cobro.mensaje,
            }
        if not cobro.aprobado:
            raise HTTPException(status_code=402, detail=cobro.mensaje)

        factura_id = await registrar_cobro(
            sesion,
            codigo=codigo,
            usuario_id=int(usuario["id"]),
            es_admin=usuario["rol"] == "administrador",
            metodo=datos.metodo,
            referencia=cobro.referencia,
            proveedor=cobro.proveedor,
            facturacion=datos.facturacion,
        )
        await sesion.commit()
    except HTTPException:
        await sesion.rollback()
        raise
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)

    detalle = (
        await sesion.execute(
            text(
                """
                SELECT TRIM(b.codigo) AS codigo,
                       b.precio,
                       b.pasajero_nombre,
                       b.pasajero_documento,
                       b.viaje_id,
                       b.asiento_id,
                       a.numero AS asiento_numero,
                       v.salida,
                       co.nombre AS origen,
                       cd.nombre AS destino,
                       p.referencia_ext,
                       p.monto,
                       p.metodo,
                       p.proveedor,
                       p.estado AS estado_pago,
                       p.pagado_en
                  FROM boletos b
                  JOIN asientos a ON a.id = b.asiento_id
                  JOIN viajes v ON v.id = b.viaje_id
                  JOIN rutas r ON r.id = v.ruta_id
                  JOIN ciudades co ON co.id = r.origen_id
                  JOIN ciudades cd ON cd.id = r.destino_id
                  JOIN pagos p ON p.boleto_id = b.id
                 WHERE b.codigo = :codigo
                """
            ),
            {"codigo": codigo},
        )
    ).mappings().one()
    datos_qr = fila_a_dict(detalle)
    qr = png_base64(
        {
            "codigo": datos_qr["codigo"],
            "pasajero": datos_qr["pasajero_nombre"],
            "documento": datos_qr["pasajero_documento"],
            "origen": datos_qr["origen"],
            "destino": datos_qr["destino"],
            "salida": datos_qr["salida"],
            "asiento": datos_qr["asiento_numero"],
            "referencia": datos_qr["referencia_ext"],
            "metodo": datos_qr["metodo"],
        }
    )
    await publicar_asiento(sesion, int(detalle["viaje_id"]), int(detalle["asiento_id"]))
    try:
        factura = resumen(await completar_emision(sesion, factura_id))
    except Exception:
        log.exception("La factura %s quedó pendiente de autorización", factura_id)
        factura = resumen(await _leer(sesion, factura_id))
    return {
        "codigo": datos_qr["codigo"],
        "estado": "pagado",
        "precio": datos_qr["precio"],
        "asiento_numero": datos_qr["asiento_numero"],
        "origen": datos_qr["origen"],
        "destino": datos_qr["destino"],
        "salida": datos_qr["salida"],
        "pasajero_nombre": datos_qr["pasajero_nombre"],
        "pago": {
            "referencia_ext": datos_qr["referencia_ext"],
            "monto": datos_qr["monto"],
            "metodo": datos_qr["metodo"],
            "proveedor": datos_qr["proveedor"],
            "estado": datos_qr["estado_pago"],
            "pagado_en": datos_qr["pagado_en"],
            "mensaje": cobro.mensaje,
        },
        "qr_png_base64": qr,
        "factura": factura,
    }


@router.post("/{codigo}/preparar")
async def preparar(
    codigo: str,
    datos: PagarIn,
    usuario: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    """Abre un cobro pendiente. Lo cierra el webhook firmado, no esta llamada."""
    codigo = codigo.strip().upper()
    try:
        bloqueado = (
            await sesion.execute(
                text(
                    """
                    SELECT id, estado, usuario_id, precio, (reservado_hasta < NOW()) AS vencida
                      FROM boletos WHERE codigo = :codigo FOR UPDATE
                    """
                ),
                {"codigo": codigo},
            )
        ).mappings().first()
        if bloqueado is None:
            raise HTTPException(status_code=404, detail="Boleto no encontrado")
        if bloqueado["usuario_id"] != usuario["id"] and usuario["rol"] != "administrador":
            raise HTTPException(status_code=403, detail="No puede pagar este boleto")
        if bloqueado["estado"] != "reservado" or bloqueado["vencida"]:
            raise HTTPException(status_code=409, detail="La reserva no está vigente")
        if not await metodo_habilitado(sesion, datos.metodo):
            raise HTTPException(status_code=422, detail="Ese método de pago está desactivado")
        proveedor = obtener_proveedor(datos.metodo)
        if proveedor is None:
            raise HTTPException(status_code=422, detail="Método de pago no disponible")
        try:
            cobro = await proveedor.iniciar(
                SolicitudPago(
                    boleto_codigo=codigo,
                    monto=bloqueado["precio"],
                    referencia_ext=datos.referencia_ext,
                    metodo=datos.metodo,
                    ultimos4=(datos.ultimos4 or "").strip(),
                )
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail="La pasarela no pudo abrir el cobro") from exc
        await guardar_intencion(
            sesion,
            boleto_id=int(bloqueado["id"]),
            usuario_id=int(bloqueado["usuario_id"]),
            metodo=datos.metodo,
            client_tx_id=datos.referencia_ext,
            id_externo=cobro.id_externo,
            monto=bloqueado["precio"],
            proveedor=cobro.proveedor,
            facturacion=datos.facturacion,
        )
        await sesion.commit()
    except HTTPException:
        await sesion.rollback()
        raise
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)
    return {
        "estado": "pendiente",
        "codigo": codigo,
        "client_tx_id": datos.referencia_ext,
        "redireccion": cobro.redireccion,
        "qr_texto": cobro.qr_texto,
        "id_externo": cobro.id_externo,
        "mensaje": cobro.mensaje,
    }


@router.post("/{codigo}/cancelar")
async def cancelar(
    codigo: str,
    usuario: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    codigo = codigo.strip().upper()
    try:
        bloqueado = (
            await sesion.execute(
                text(
                    """
                    SELECT id, estado, usuario_id, viaje_id, asiento_id
                      FROM boletos
                     WHERE codigo = :codigo
                     FOR UPDATE
                    """
                ),
                {"codigo": codigo},
            )
        ).mappings().first()
        if bloqueado is None:
            raise HTTPException(status_code=404, detail="Boleto no encontrado")
        if bloqueado["usuario_id"] != usuario["id"] and usuario["rol"] != "administrador":
            raise HTTPException(status_code=403, detail="No puede cancelar este boleto")
        if bloqueado["estado"] not in ("reservado", "pagado"):
            raise HTTPException(status_code=409, detail="El boleto no se puede cancelar")
        if bloqueado["estado"] == "pagado":
            await sesion.execute(
                text("UPDATE pagos SET estado = 'rechazado' WHERE boleto_id = :id"),
                {"id": bloqueado["id"]},
            )
        await sesion.execute(
            text("UPDATE boletos SET estado = 'cancelado' WHERE id = :id"),
            {"id": bloqueado["id"]},
        )
        await sesion.commit()
    except HTTPException:
        await sesion.rollback()
        raise
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)

    await publicar_asiento(sesion, int(bloqueado["viaje_id"]), int(bloqueado["asiento_id"]))
    boleto = await _leer_boleto(sesion, codigo)
    return boleto
