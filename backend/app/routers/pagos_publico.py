"""Métodos públicos, código QR y webhooks de las pasarelas."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import text

from app.cobro import cerrar_intencion
from app.config import settings
from app.dependencias import exigir_admin, obtener_sesion
from app.emision import completar_emision
from app.pagos import (
    METODOS,
    confirmar_payphone,
    consultar_deuna,
    credenciales_de,
    deuna_aprobado,
    firma_valida,
    modo_de,
    payphone_aprobado,
    referencia_deuna,
    secreto_webhook,
)

router = APIRouter()

NOMBRES = {
    "deuna": "DeUna!",
    "tarjeta": "Tarjeta de crédito o débito",
    "payphone": "PayPhone",
}
DETALLES = {
    "deuna": "Billetera Banco Pichincha. Pague con QR en la app.",
    "tarjeta": "Visa, Mastercard y otras. El número no pasa por La Maná.",
    "payphone": "Cajita de pagos: saldo PayPhone o tarjeta.",
}


def _publico(codigo: str) -> dict:
    return {"codigo": codigo, "nombre": NOMBRES[codigo], "detalle": DETALLES[codigo]}


def _estado_admin(codigo: str, activo: bool) -> dict:
    listas, faltan = credenciales_de(codigo)
    return {
        "codigo": codigo,
        "nombre": NOMBRES[codigo],
        "detalle": DETALLES[codigo],
        "activo": activo,
        "modo": modo_de(codigo),
        "credenciales_listas": listas,
        "faltan": faltan,
    }


@router.get("/pagos/metodos")
async def metodos(sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (await sesion.execute(text("SELECT codigo, activo FROM metodos_pago"))).mappings().all()
    activos = {fila["codigo"]: bool(fila["activo"]) for fila in filas}
    return [_publico(codigo) for codigo in METODOS if activos.get(codigo, True)]


@router.get("/admin/pagos/metodos")
async def metodos_admin(_: dict = Depends(exigir_admin), sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (await sesion.execute(text("SELECT codigo, activo FROM metodos_pago"))).mappings().all()
    activos = {fila["codigo"]: bool(fila["activo"]) for fila in filas}
    return [_estado_admin(codigo, activos.get(codigo, True)) for codigo in METODOS]


@router.patch("/admin/pagos/metodos/{codigo}")
async def cambiar_metodo(
    codigo: str,
    cuerpo: dict,
    _: dict = Depends(exigir_admin),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    if codigo not in METODOS:
        raise HTTPException(status_code=404, detail="Método de pago desconocido")
    if "activo" not in cuerpo or not isinstance(cuerpo["activo"], bool):
        raise HTTPException(status_code=422, detail="Indique activo como verdadero o falso")
    await sesion.execute(
        text("UPDATE metodos_pago SET activo = :activo WHERE codigo = :codigo"),
        {"activo": 1 if cuerpo["activo"] else 0, "codigo": codigo},
    )
    await sesion.commit()
    fila = (await sesion.execute(text("SELECT activo FROM metodos_pago WHERE codigo = :codigo"), {"codigo": codigo})).first()
    return _estado_admin(codigo, bool(fila[0]) if fila else cuerpo["activo"])


@router.get("/pagos/qr")
async def qr(texto: str = Query(min_length=4, max_length=180)):
    import io

    import qrcode

    imagen = qrcode.make(texto)
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    return Response(content=buffer.getvalue(), media_type="image/png")


@router.post("/pagos/webhooks/deuna")
async def webhook_deuna(request: Request, sesion: AsyncSession = Depends(obtener_sesion)):
    cuerpo = await request.body()
    firma = request.headers.get("x-deuna-signature") or request.headers.get("x-lamana-firma")
    if not firma_valida(cuerpo, firma, secreto_webhook()):
        raise HTTPException(status_code=401, detail="Firma del webhook inválida")
    try:
        datos = json.loads(cuerpo.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="El webhook no trae JSON") from exc
    if not isinstance(datos, dict):
        raise HTTPException(status_code=422, detail="El webhook no trae un objeto")
    referencia = referencia_deuna(datos)
    if not referencia:
        raise HTTPException(status_code=422, detail="Falta la referencia del cobro")
    if settings.pagos_modo.strip().lower() == "live" and settings.deuna_api_key.strip():
        token = str(datos.get("token") or datos.get("order_token") or "")
        if token:
            datos = await consultar_deuna(token)
    resultado = await cerrar_intencion(sesion, referencia, deuna_aprobado(datos) or _sandbox_ok(datos), datos.get("id"))
    return await _emitir(sesion, resultado)


@router.post("/pagos/webhooks/payphone")
async def webhook_payphone(request: Request, sesion: AsyncSession = Depends(obtener_sesion)):
    cuerpo = await request.body()
    firma = request.headers.get("x-lamana-firma")
    en_vivo = settings.pagos_modo.strip().lower() == "live" and bool(settings.payphone_token.strip())
    if not en_vivo and not firma_valida(cuerpo, firma, secreto_webhook()):
        raise HTTPException(status_code=401, detail="Firma del webhook inválida")
    try:
        datos = json.loads(cuerpo.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="El webhook no trae JSON") from exc
    client_tx = str(datos.get("clientTransactionId") or datos.get("clientTxId") or "").strip()
    id_externo = str(datos.get("id") or "")
    if not client_tx:
        raise HTTPException(status_code=422, detail="Falta clientTransactionId")
    if en_vivo:
        if not id_externo:
            raise HTTPException(status_code=422, detail="Falta el id de PayPhone")
        datos = await confirmar_payphone(id_externo, client_tx)
        monto = await _monto_intencion(sesion, client_tx)
        aprobado = payphone_aprobado(datos, monto)
    else:
        aprobado = _sandbox_ok(datos)
    resultado = await cerrar_intencion(sesion, client_tx, aprobado, id_externo or None)
    return await _emitir(sesion, resultado)


def _sandbox_ok(datos: dict) -> bool:
    estado = str(datos.get("status") or datos.get("transactionStatus") or "approved").lower()
    return estado in {"approved", "succeeded", "3"} or datos.get("statusCode") in (3, "3")


async def _monto_intencion(sesion: AsyncSession, client_tx: str):
    from decimal import Decimal

    fila = (
        await sesion.execute(
            text("SELECT monto FROM intenciones_pago WHERE client_tx_id = :tx"),
            {"tx": client_tx},
        )
    ).first()
    if fila is None:
        raise HTTPException(status_code=404, detail="No hay un cobro con esa referencia")
    return Decimal(str(fila[0]))


async def _emitir(sesion: AsyncSession, resultado: dict) -> dict:
    if resultado.get("estado") == "aprobado" and not resultado.get("repetido"):
        await sesion.commit()
        factura_id = resultado.get("factura_id")
        if factura_id:
            try:
                await completar_emision(sesion, int(factura_id))
            except Exception:
                pass
    elif resultado.get("estado") == "rechazado":
        await sesion.commit()
    else:
        await sesion.rollback()
    return {clave: valor for clave, valor in resultado.items() if clave != "factura_id"}
