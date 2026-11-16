from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.consulta_identificacion import consultar_identificacion
from app.dependencias import exigir_transporte, obtener_sesion, usuario_actual
from app.emision import _para_ride, reenviar, resumen
from app.errores import traducir_error_mysql
from app.esquemas import EmisorIn
from app.identificacion import validar_identificacion
from app.presentacion import fila_a_dict
from app.ride import generar_ride

router = APIRouter()


def _pdf(factura: dict) -> Response:
    pdf = generar_ride(_para_ride(factura))
    nombre = f"RIDE-{factura['numero']}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{nombre}"'},
    )


def _xml(factura: dict) -> Response:
    cuerpo = factura.get("xml_autorizado") or factura["xml_comprobante"]
    nombre = f"Factura-{factura['numero']}.xml"
    return Response(
        content=cuerpo.encode("utf-8"),
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


async def _factura(sesion: AsyncSession, factura_id: int) -> dict:
    fila = (
        await sesion.execute(
            text(
                """
                SELECT f.*, d.descripcion, d.tarifa_iva, d.ruta, d.salida, d.asiento, d.pasajero
                  FROM facturas f
                  JOIN factura_detalles d ON d.factura_id = f.id
                 WHERE f.id = :id
                """
            ),
            {"id": factura_id},
        )
    ).mappings().first()
    if fila is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return fila_a_dict(fila)


def _exigir_dueno(factura: dict, usuario: dict) -> None:
    if factura["usuario_id"] != usuario["id"] and usuario["rol"] != "administrador":
        raise HTTPException(status_code=403, detail="No puede ver esta factura")


@router.get("/facturacion/consulta")
async def consulta(
    tipo: str = Query(min_length=3, max_length=20),
    identificacion: str = Query(min_length=5, max_length=20),
    _: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    numero = identificacion.strip().upper()
    mensaje = validar_identificacion(tipo, numero)
    if mensaje:
        raise HTTPException(status_code=422, detail=mensaje)
    if tipo not in ("cedula", "ruc"):
        return {"encontrado": False, "origen": None, "identificacion": numero, "tipo": tipo}
    return await consultar_identificacion(sesion, tipo, numero)


@router.get("/facturacion/mias")
async def mias(
    usuario: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT f.id, f.numero, f.clave_acceso, f.fecha_emision, f.estado, f.total, f.iva,
                       f.razon_social_comprador, f.identificacion_comprador,
                       d.ruta, d.salida, d.asiento, d.pasajero
                  FROM facturas f
                  JOIN factura_detalles d ON d.factura_id = f.id
                 WHERE f.usuario_id = :usuario
                 ORDER BY f.id DESC
                """
            ),
            {"usuario": usuario["id"]},
        )
    ).mappings().all()
    return [fila_a_dict(fila) for fila in filas]


@router.get("/facturacion/{factura_id}/ride")
async def ride_cliente(
    factura_id: int,
    usuario: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    factura = await _factura(sesion, factura_id)
    _exigir_dueno(factura, usuario)
    return _pdf(factura)


@router.get("/facturacion/{factura_id}/xml")
async def xml_cliente(
    factura_id: int,
    usuario: dict = Depends(usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    factura = await _factura(sesion, factura_id)
    _exigir_dueno(factura, usuario)
    return _xml(factura)


@router.get("/admin/facturas")
async def listar_facturas(
    estado: str | None = None,
    identificacion: str | None = None,
    desde: str | None = None,
    hasta: str | None = None,
    metodo: str | None = None,
    _: dict = Depends(exigir_transporte),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    metodo_limpio = (metodo or "").strip() or None
    if metodo_limpio and metodo_limpio not in ("deuna", "tarjeta", "payphone"):
        raise HTTPException(status_code=422, detail="El filtro de pago solo admite DeUna, tarjeta o PayPhone")
    filas = (
        await sesion.execute(
            text(
                """
                SELECT f.id, f.numero, f.clave_acceso, f.fecha_emision, f.estado, f.total, f.iva,
                       f.identificacion_comprador, f.razon_social_comprador, f.email_comprador,
                       f.ambiente, f.mensaje_sri, f.firma_omitida,
                       d.ruta, d.salida, d.asiento, d.pasajero, p.metodo
                  FROM facturas f
                  JOIN factura_detalles d ON d.factura_id = f.id
                  LEFT JOIN pagos p ON p.boleto_id = f.boleto_id
                 WHERE (:estado IS NULL OR f.estado = :estado)
                   AND (:identificacion IS NULL OR f.identificacion_comprador = :identificacion)
                   AND (:desde IS NULL OR DATE(f.fecha_emision) >= :desde)
                   AND (:hasta IS NULL OR DATE(f.fecha_emision) <= :hasta)
                   AND (:metodo IS NULL OR p.metodo = :metodo)
                 ORDER BY f.id DESC
                 LIMIT 200
                """
            ),
            {
                "estado": (estado or "").strip() or None,
                "identificacion": (identificacion or "").strip() or None,
                "desde": (desde or "").strip() or None,
                "hasta": (hasta or "").strip() or None,
                "metodo": metodo_limpio,
            },
        )
    ).mappings().all()
    return [fila_a_dict(fila) for fila in filas]


@router.post("/admin/facturas/{factura_id}/reenviar")
async def reenviar_factura(
    factura_id: int,
    _: dict = Depends(exigir_transporte),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    try:
        factura = await reenviar(sesion, factura_id)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)
    return resumen(factura)


@router.get("/admin/facturas/{factura_id}/ride")
async def ride_admin(
    factura_id: int,
    _: dict = Depends(exigir_transporte),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    return _pdf(await _factura(sesion, factura_id))


@router.get("/admin/facturas/{factura_id}/xml")
async def xml_admin(
    factura_id: int,
    _: dict = Depends(exigir_transporte),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    return _xml(await _factura(sesion, factura_id))


@router.get("/admin/emisor")
async def leer_emisor(
    _: dict = Depends(exigir_transporte),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    fila = (await sesion.execute(text("SELECT * FROM emisor WHERE id = 1"))).mappings().first()
    if fila is None:
        raise HTTPException(status_code=404, detail="No hay emisor configurado")
    return fila_a_dict(fila)


@router.put("/admin/emisor")
async def guardar_emisor(
    datos: EmisorIn,
    _: dict = Depends(exigir_transporte),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    try:
        actualizado = await sesion.execute(
            text(
                """
                UPDATE emisor
                   SET ruc = :ruc,
                       razon_social = :razon_social,
                       nombre_comercial = :nombre_comercial,
                       establecimiento = :establecimiento,
                       punto_emision = :punto_emision,
                       direccion_matriz = :direccion_matriz,
                       obligado_contabilidad = :obligado_contabilidad,
                       ambiente = :ambiente,
                       tarifa_iva_pasaje = :tarifa_iva_pasaje
                 WHERE id = 1
                """
            ),
            {
                "ruc": datos.ruc,
                "razon_social": datos.razon_social,
                "nombre_comercial": datos.nombre_comercial,
                "establecimiento": datos.establecimiento,
                "punto_emision": datos.punto_emision,
                "direccion_matriz": datos.direccion_matriz,
                "obligado_contabilidad": int(datos.obligado_contabilidad),
                "ambiente": datos.ambiente,
                "tarifa_iva_pasaje": f"{datos.tarifa_iva_pasaje:.2f}",
            },
        )
        if actualizado.rowcount != 1:
            raise HTTPException(status_code=404, detail="No hay emisor configurado")
        await sesion.commit()
    except HTTPException:
        await sesion.rollback()
        raise
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)
    fila = (await sesion.execute(text("SELECT * FROM emisor WHERE id = 1"))).mappings().one()
    return fila_a_dict(fila)
