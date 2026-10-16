import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencias import obtener_sesion, usuario_actual
from app.errores import CodigoDuplicado, traducir_error_mysql
from app.esquemas import PagarIn, ReservarIn
from app.presentacion import fila_a_dict
from app.qr import png_base64
from app.ws import publicar_asiento

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

        await sesion.execute(
            text(
                """
                INSERT INTO pagos (boleto_id, referencia_ext, monto, estado, pagado_en)
                VALUES (:boleto_id, :referencia, :monto, 'aprobado', NOW())
                """
            ),
            {
                "boleto_id": bloqueado["id"],
                "referencia": datos.referencia_ext,
                "monto": bloqueado["precio"],
            },
        )
        await sesion.execute(
            text("UPDATE boletos SET estado = 'pagado' WHERE id = :id"),
            {"id": bloqueado["id"]},
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
        }
    )
    await publicar_asiento(sesion, int(detalle["viaje_id"]), int(detalle["asiento_id"]))
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
            "estado": datos_qr["estado_pago"],
            "pagado_en": datos_qr["pagado_en"],
        },
        "qr_png_base64": qr,
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
