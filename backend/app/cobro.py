"""Cierra un boleto reservado: pago, factura y marca de la intención."""

import json

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.emision import registrar_factura
from app.errores import traducir_error_mysql
from app.esquemas import FacturacionIn


async def metodo_habilitado(sesion: AsyncSession, codigo: str) -> bool:
    fila = (
        await sesion.execute(
            text("SELECT activo FROM metodos_pago WHERE codigo = :codigo"),
            {"codigo": codigo},
        )
    ).first()
    if fila is None:
        return True
    return bool(fila[0])


async def guardar_intencion(
    sesion: AsyncSession,
    *,
    boleto_id: int,
    usuario_id: int,
    metodo: str,
    client_tx_id: str,
    id_externo: str | None,
    monto,
    proveedor: str,
    facturacion: FacturacionIn,
) -> None:
    await sesion.execute(
        text(
            """
            INSERT INTO intenciones_pago
              (boleto_id, usuario_id, metodo, client_tx_id, id_externo, monto, estado, proveedor, facturacion)
            VALUES
              (:boleto_id, :usuario_id, :metodo, :client_tx_id, :id_externo, :monto, 'pendiente', :proveedor, :facturacion)
            """
        ),
        {
            "boleto_id": boleto_id,
            "usuario_id": usuario_id,
            "metodo": metodo,
            "client_tx_id": client_tx_id[:64],
            "id_externo": id_externo,
            "monto": monto,
            "proveedor": proveedor[:80],
            "facturacion": facturacion.model_dump_json(),
        },
    )


async def registrar_cobro(
    sesion: AsyncSession,
    *,
    codigo: str,
    usuario_id: int,
    es_admin: bool,
    metodo: str,
    referencia: str,
    proveedor: str,
    facturacion: FacturacionIn,
) -> int:
    bloqueado = (
        await sesion.execute(
            text(
                """
                SELECT id, estado, usuario_id, precio, (reservado_hasta < NOW()) AS vencida
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
    if bloqueado["usuario_id"] != usuario_id and not es_admin:
        raise HTTPException(status_code=403, detail="No puede pagar este boleto")
    if bloqueado["estado"] != "reservado":
        raise HTTPException(status_code=409, detail="El boleto no está reservado")
    if bloqueado["vencida"]:
        raise HTTPException(status_code=409, detail="La reserva expiró")
    try:
        await sesion.execute(
            text(
                """
                INSERT INTO pagos (boleto_id, referencia_ext, monto, metodo, proveedor, estado, pagado_en)
                VALUES (:boleto_id, :referencia, :monto, :metodo, :proveedor, 'aprobado', NOW())
                """
            ),
            {
                "boleto_id": bloqueado["id"],
                "referencia": referencia[:64],
                "monto": bloqueado["precio"],
                "metodo": metodo,
                "proveedor": proveedor[:80],
            },
        )
    except SQLAlchemyError as exc:
        traducir_error_mysql(exc)
    await sesion.execute(
        text("UPDATE boletos SET estado = 'pagado' WHERE id = :id"),
        {"id": bloqueado["id"]},
    )
    return await registrar_factura(
        sesion,
        boleto_id=int(bloqueado["id"]),
        usuario_id=int(bloqueado["usuario_id"]),
        comprador=facturacion,
        metodo=metodo,
    )


async def cerrar_intencion(sesion: AsyncSession, client_tx_id: str, aprobado: bool, id_externo: str | None = None) -> dict:
    intento = (
        await sesion.execute(
            text(
                """
                SELECT id, boleto_id, usuario_id, metodo, client_tx_id, monto, estado, proveedor, facturacion
                  FROM intenciones_pago
                 WHERE client_tx_id = :tx
                 FOR UPDATE
                """
            ),
            {"tx": client_tx_id},
        )
    ).mappings().first()
    if intento is None:
        raise HTTPException(status_code=404, detail="No hay un cobro con esa referencia")
    if intento["estado"] == "aprobado":
        return {"estado": "aprobado", "repetido": True, "client_tx_id": client_tx_id}
    if not aprobado:
        await sesion.execute(
            text("UPDATE intenciones_pago SET estado = 'rechazado' WHERE id = :id"),
            {"id": intento["id"]},
        )
        return {"estado": "rechazado", "repetido": False, "client_tx_id": client_tx_id}
    crudo = intento["facturacion"] or "{}"
    datos = json.loads(crudo) if isinstance(crudo, str) else crudo
    facturacion = FacturacionIn.model_validate(datos)
    codigo = (
        await sesion.execute(
            text("SELECT TRIM(codigo) FROM boletos WHERE id = :id"),
            {"id": intento["boleto_id"]},
        )
    ).scalar()
    factura_id = await registrar_cobro(
        sesion,
        codigo=str(codigo).strip(),
        usuario_id=int(intento["usuario_id"]),
        es_admin=True,
        metodo=intento["metodo"],
        referencia=client_tx_id,
        proveedor=intento["proveedor"],
        facturacion=facturacion,
    )
    await sesion.execute(
        text(
            """
            UPDATE intenciones_pago
               SET estado = 'aprobado', id_externo = COALESCE(:externo, id_externo)
             WHERE id = :id
            """
        ),
        {"id": intento["id"], "externo": id_externo},
    )
    return {
        "estado": "aprobado",
        "repetido": False,
        "client_tx_id": client_tx_id,
        "factura_id": factura_id,
        "boleto_codigo": str(codigo).strip(),
    }
