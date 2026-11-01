"""Indicadores del panel. Cada rol solo recibe su módulo."""

import calendar
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencias import exigir_panel, obtener_sesion
from app.tiempo import ahora_colombia

router = APIRouter()


def _num(valor) -> float:
    return round(float(valor or 0), 2)


def _variacion(actual, anterior, decimales=2) -> dict:
    actual_n = round(float(actual or 0), decimales)
    anterior_n = round(float(anterior or 0), decimales)
    if anterior_n == 0:
        cambio = None
    else:
        cambio = round((actual_n - anterior_n) / anterior_n * 100, 1)
    return {"valor": actual_n, "anterior": anterior_n, "variacion": cambio}


def _iso(valor):
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.strftime("%Y-%m-%d %H:%M")
    if isinstance(valor, date):
        return valor.isoformat()
    return str(valor)


def _periodo_previo(desde: date, hasta: date) -> tuple[date, date]:
    dias = (hasta - desde).days
    fin = desde - timedelta(days=1)
    return fin - timedelta(days=dias), fin


def _mes_previo(hoy: date) -> tuple[date, date, date, date]:
    inicio = hoy.replace(day=1)
    if inicio.month == 1:
        previo = date(inicio.year - 1, 12, 1)
    else:
        previo = date(inicio.year, inicio.month - 1, 1)
    ultimo = calendar.monthrange(previo.year, previo.month)[1]
    return inicio, hoy, previo, previo.replace(day=min(hoy.day, ultimo))


@router.get("/admin/dashboard/resumen")
async def resumen_dashboard(
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    usuario: dict = Depends(exigir_panel),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    hoy = ahora_colombia().date()
    hasta = hasta or hoy
    desde = desde or (hasta - timedelta(days=29))
    if desde > hasta:
        raise HTTPException(status_code=422, detail="La fecha inicial no puede ser posterior a la final")
    if (hasta - desde).days > 366:
        raise HTTPException(status_code=422, detail="El rango máximo es de 366 días")

    rol = usuario["rol"]
    ver_transporte = rol in ("administrador", "operador_transporte")
    ver_turismo = rol in ("administrador", "operador_turismo")
    ver_taxi = rol in ("administrador", "operador_taxi")
    previo_desde, previo_hasta = _periodo_previo(desde, hasta)
    ayer = hoy - timedelta(days=1)
    mes_desde, mes_hasta, mes_prev_desde, mes_prev_hasta = _mes_previo(hoy)

    cuerpo: dict = {
        "rol": rol,
        "desde": desde.isoformat(),
        "hasta": hasta.isoformat(),
        "demo": False,
        "avisos": [],
    }

    if ver_transporte:
        transporte = await _transporte(sesion, hoy, ayer, desde, hasta, previo_desde, previo_hasta, mes_desde, mes_hasta, mes_prev_desde, mes_prev_hasta)
        cuerpo["transporte"] = transporte
        cuerpo["demo"] = cuerpo["demo"] or transporte["demo"]
        cuerpo["avisos"].append({
            "id": "ventas-hoy",
            "texto": f"Ventas de boletos hoy: ${transporte['kpis']['ventas_hoy']['valor']:.2f}",
        })

    if ver_turismo:
        turismo = await _turismo(sesion)
        cuerpo["turismo"] = turismo
        cuerpo["demo"] = cuerpo["demo"] or turismo["demo"]
        cuerpo["avisos"].append({"id": "mensajes", "texto": f"{turismo['mensajes']} mensajes del portal"})
        cuerpo["avisos"].append({"id": "eventos", "texto": f"{turismo['eventos_proximos']} eventos próximos"})

    if ver_taxi:
        taxi = await _taxi(sesion, hoy, ayer, desde, hasta)
        cuerpo["taxi"] = taxi
        cuerpo["demo"] = cuerpo["demo"] or taxi["demo"]
        cuerpo["avisos"].append({"id": "taxis", "texto": f"{int(taxi['kpis']['en_linea']['valor'])} taxis en línea"})

    return cuerpo


async def _escalar(sesion: AsyncSession, sql: str, params: dict):
    return (await sesion.execute(text(sql), params)).scalar_one()


async def _transporte(sesion, hoy, ayer, desde, hasta, previo_desde, previo_hasta, mes_desde, mes_hasta, mes_prev_desde, mes_prev_hasta):
    async def ventas(inicio, fin):
        fila = (
            await sesion.execute(
                text(
                    """
                    SELECT COALESCE(SUM(monto), 0), COUNT(*)
                      FROM pagos
                     WHERE estado = 'aprobado'
                       AND pagado_en IS NOT NULL
                       AND DATE(pagado_en) BETWEEN :inicio AND :fin
                    """
                ),
                {"inicio": inicio, "fin": fin},
            )
        ).one()
        return _num(fila[0]), int(fila[1])

    ventas_hoy, _ = await ventas(hoy, hoy)
    ventas_ayer, _ = await ventas(ayer, ayer)
    ventas_mes, _ = await ventas(mes_desde, mes_hasta)
    ventas_mes_prev, _ = await ventas(mes_prev_desde, mes_prev_hasta)
    _, boletos = await ventas(desde, hasta)
    _, boletos_prev = await ventas(previo_desde, previo_hasta)

    async def salidas(dia):
        return int(
            await _escalar(
                sesion,
                """
                SELECT COUNT(*) FROM viajes
                 WHERE estado <> 'cancelado' AND DATE(salida) = :dia
                """,
                {"dia": dia},
            )
        )

    async def ocupacion(dia):
        ocupados = int(
            await _escalar(
                sesion,
                """
                SELECT COUNT(*)
                  FROM boletos b
                  JOIN viajes v ON v.id = b.viaje_id
                 WHERE DATE(v.salida) = :dia
                   AND v.estado <> 'cancelado'
                   AND b.estado IN ('pagado', 'reservado', 'usado')
                """,
                {"dia": dia},
            )
        )
        puestos = int(
            await _escalar(
                sesion,
                """
                SELECT COUNT(*)
                  FROM viajes v
                  JOIN asientos a ON a.bus_id = v.bus_id
                 WHERE DATE(v.salida) = :dia AND v.estado <> 'cancelado'
                """,
                {"dia": dia},
            )
        )
        return round(100 * ocupados / puestos, 1) if puestos else 0

    filas_dia = (
        await sesion.execute(
            text(
                """
                SELECT DATE(pagado_en) AS dia, COALESCE(SUM(monto), 0) AS total, COUNT(*) AS boletos
                  FROM pagos
                 WHERE estado = 'aprobado'
                   AND pagado_en IS NOT NULL
                   AND DATE(pagado_en) BETWEEN :desde AND :hasta
                 GROUP BY DATE(pagado_en)
                """
            ),
            {"desde": desde, "hasta": hasta},
        )
    ).mappings().all()
    por_fecha = {fila["dia"]: fila for fila in filas_dia}
    ventas_por_dia = []
    cursor = desde
    while cursor <= hasta:
        fila = por_fecha.get(cursor)
        ventas_por_dia.append({
            "fecha": cursor.isoformat(),
            "total": _num(fila["total"]) if fila else 0,
            "boletos": int(fila["boletos"]) if fila else 0,
        })
        cursor += timedelta(days=1)

    rutas = (
        await sesion.execute(
            text(
                """
                SELECT CONCAT(co.nombre, ' → ', cd.nombre) AS ruta,
                       COALESCE(SUM(oc.ocupados), 0) AS ocupados,
                       COALESCE(SUM(bu.capacidad), 0) AS puestos
                  FROM viajes v
                  JOIN rutas r ON r.id = v.ruta_id
                  JOIN ciudades co ON co.id = r.origen_id
                  JOIN ciudades cd ON cd.id = r.destino_id
                  JOIN buses bu ON bu.id = v.bus_id
                  LEFT JOIN (
                    SELECT viaje_id, COUNT(*) AS ocupados
                      FROM boletos
                     WHERE estado IN ('pagado', 'reservado', 'usado')
                     GROUP BY viaje_id
                  ) oc ON oc.viaje_id = v.id
                 WHERE v.estado <> 'cancelado'
                   AND DATE(v.salida) BETWEEN :desde AND :hasta
                 GROUP BY r.id, co.nombre, cd.nombre
                 ORDER BY ocupados DESC, puestos DESC
                 LIMIT 6
                """
            ),
            {"desde": desde, "hasta": hasta},
        )
    ).mappings().all()
    ocupacion_por_ruta = []
    for fila in rutas:
        puestos = int(fila["puestos"] or 0)
        ocupados = int(fila["ocupados"] or 0)
        ocupacion_por_ruta.append({
            "ruta": fila["ruta"],
            "ocupados": ocupados,
            "puestos": puestos,
            "ocupacion": round(100 * ocupados / puestos, 1) if puestos else 0,
        })

    recientes = (
        await sesion.execute(
            text(
                """
                SELECT p.id, p.monto, p.estado, p.pagado_en, p.proveedor, p.referencia_ext,
                       co.nombre AS origen, cd.nombre AS destino
                  FROM pagos p
                  JOIN boletos b ON b.id = p.boleto_id
                  JOIN viajes v ON v.id = b.viaje_id
                  JOIN rutas r ON r.id = v.ruta_id
                  JOIN ciudades co ON co.id = r.origen_id
                  JOIN ciudades cd ON cd.id = r.destino_id
                 ORDER BY p.id DESC
                 LIMIT 8
                """
            )
        )
    ).mappings().all()
    ventas_recientes = [
        {
            "id": int(fila["id"]),
            "ruta": f"{fila['origen']} → {fila['destino']}",
            "monto": _num(fila["monto"]),
            "estado": fila["estado"],
            "fecha": _iso(fila["pagado_en"]),
            "demo": fila["proveedor"] == "demo" or str(fila["referencia_ext"]).startswith("DEMO-DASH-"),
        }
        for fila in recientes
    ]
    demo_en_rango = int(
        await _escalar(
            sesion,
            """
            SELECT COUNT(*) FROM pagos
             WHERE estado = 'aprobado'
               AND (proveedor = 'demo' OR referencia_ext LIKE 'DEMO-DASH-%')
               AND DATE(pagado_en) BETWEEN :desde AND :hasta
            """,
            {"desde": desde, "hasta": hasta},
        )
    )

    return {
        "demo": demo_en_rango > 0 or any(item["demo"] for item in ventas_recientes),
        "kpis": {
            "ventas_hoy": _variacion(ventas_hoy, ventas_ayer),
            "ventas_mes": _variacion(ventas_mes, ventas_mes_prev),
            "boletos": _variacion(boletos, boletos_prev, 0),
            "viajes_activos": _variacion(await salidas(hoy), await salidas(ayer), 0),
            "ocupacion": _variacion(await ocupacion(hoy), await ocupacion(ayer), 1),
        },
        "ventas_por_dia": ventas_por_dia,
        "ocupacion_por_ruta": ocupacion_por_ruta,
        "ventas_recientes": ventas_recientes,
    }


async def _turismo(sesion):
    fichas = int(await _escalar(sesion, "SELECT COUNT(*) FROM turismo_fichas WHERE activo = 1", {}))
    atractivos = int(
        await _escalar(sesion, "SELECT COUNT(*) FROM turismo_fichas WHERE activo = 1 AND tipo = 'atractivo'", {})
    )
    eventos = int(await _escalar(sesion, "SELECT COUNT(*) FROM turismo_eventos WHERE activo = 1", {}))
    proximos = int(
        await _escalar(
            sesion,
            "SELECT COUNT(*) FROM turismo_eventos WHERE activo = 1 AND inicio >= CURDATE()",
            {},
        )
    )
    mensajes = int(await _escalar(sesion, "SELECT COUNT(*) FROM turismo_mensajes", {}))
    top = (
        await sesion.execute(
            text(
                """
                SELECT nombre, slug, zona, destacado
                  FROM turismo_fichas
                 WHERE tipo = 'atractivo' AND activo = 1
                 ORDER BY destacado DESC, orden ASC, nombre ASC
                 LIMIT 6
                """
            )
        )
    ).mappings().all()
    agenda = (
        await sesion.execute(
            text(
                """
                SELECT titulo, slug, inicio, lugar
                  FROM turismo_eventos
                 WHERE activo = 1 AND inicio >= CURDATE()
                 ORDER BY inicio ASC
                 LIMIT 6
                """
            )
        )
    ).mappings().all()
    eventos_proximos = [
        {
            "titulo": fila["titulo"],
            "slug": fila["slug"],
            "inicio": _iso(fila["inicio"]),
            "lugar": fila["lugar"],
            "demo": str(fila["slug"]).startswith("ejemplo-") or str(fila["titulo"]).startswith("Ejemplo"),
        }
        for fila in agenda
    ]
    return {
        "demo": any(item["demo"] for item in eventos_proximos),
        "fichas": fichas,
        "atractivos": atractivos,
        "eventos_publicados": eventos,
        "eventos_proximos_total": proximos,
        "mensajes": mensajes,
        "top_atractivos": [
            {
                "nombre": fila["nombre"],
                "slug": fila["slug"],
                "zona": fila["zona"],
                "destacado": bool(fila["destacado"]),
            }
            for fila in top
        ],
        "eventos_proximos": eventos_proximos,
    }


async def _taxi(sesion, hoy, ayer, desde, hasta):
    async def viajes(dia):
        return int(
            await _escalar(
                sesion,
                "SELECT COUNT(*) FROM taxi_viajes WHERE DATE(creado_en) = :dia",
                {"dia": dia},
            )
        )

    en_linea = int(
        await _escalar(
            sesion,
            """
            SELECT COUNT(*) FROM taxi_conductores
             WHERE activo = 1 AND estado = 'disponible' AND lat IS NOT NULL
            """,
            {},
        )
    )
    horas = (
        await sesion.execute(
            text(
                """
                SELECT HOUR(creado_en) AS hora, COUNT(*) AS total
                  FROM taxi_viajes
                 WHERE DATE(creado_en) BETWEEN :desde AND :hasta
                 GROUP BY HOUR(creado_en)
                """
            ),
            {"desde": desde, "hasta": hasta},
        )
    ).mappings().all()
    por_hora_map = {int(fila["hora"]): int(fila["total"]) for fila in horas}
    recientes = (
        await sesion.execute(
            text(
                """
                SELECT id, estado, destino_texto, tarifa_estimada, tarifa_final, creado_en, ejemplo
                  FROM taxi_viajes
                 ORDER BY id DESC
                 LIMIT 8
                """
            )
        )
    ).mappings().all()
    unidades = (
        await sesion.execute(
            text(
                """
                SELECT id, numero_unidad, lat, lng, estado, ejemplo
                  FROM taxi_conductores
                 WHERE activo = 1 AND estado = 'disponible' AND lat IS NOT NULL AND lng IS NOT NULL
                 ORDER BY numero_unidad
                """
            )
        )
    ).mappings().all()
    demo = int(
        await _escalar(
            sesion,
            """
            SELECT COUNT(*) FROM taxi_viajes
             WHERE ejemplo = 1 AND DATE(creado_en) BETWEEN :desde AND :hasta
            """,
            {"desde": desde, "hasta": hasta},
        )
    )
    return {
        "demo": demo > 0,
        "kpis": {
            "en_linea": {"valor": float(en_linea), "anterior": None, "variacion": None},
            "viajes_hoy": _variacion(await viajes(hoy), await viajes(ayer), 0),
        },
        "por_hora": [{"hora": hora, "total": por_hora_map.get(hora, 0)} for hora in range(24)],
        "recientes": [
            {
                "id": int(fila["id"]),
                "estado": fila["estado"],
                "destino": fila["destino_texto"],
                "tarifa": _num(fila["tarifa_final"] if fila["tarifa_final"] is not None else fila["tarifa_estimada"]),
                "fecha": _iso(fila["creado_en"]),
                "demo": bool(fila["ejemplo"]),
            }
            for fila in recientes
        ],
        "unidades": [
            {
                "id": int(fila["id"]),
                "unidad": fila["numero_unidad"],
                "lat": float(fila["lat"]),
                "lng": float(fila["lng"]),
                "estado": fila["estado"],
                "ejemplo": bool(fila["ejemplo"]),
            }
            for fila in unidades
        ],
    }
