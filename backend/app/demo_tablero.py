"""Cifras de ejemplo para que el panel no abra gráficos en blanco.

Solo se insertan si el período reciente no tiene movimiento. Los pagos usan
proveedor 'demo' y los viajes de taxi quedan con ejemplo = 1.
"""

import logging
import secrets
from datetime import datetime, timedelta

from sqlalchemy import text

from app.database import engine
from app.tiempo import ahora_colombia

log = logging.getLogger("lamana.demo")

HASH_SIN_INGRESO = "$2b$12$zD/KCMgw7MfTjSDtRWERv.pv8nU63kesJRVmhU6iiIQTT1A3UevEC"


async def asegurar_demo_tablero() -> None:
    async with engine.begin() as conexion:
        await _pasajero(conexion)
        await _boletos(conexion)
        await _taxis(conexion)
        await _evento(conexion)


async def _pasajero(conexion) -> None:
    await conexion.execute(
        text(
            """
            INSERT INTO usuarios (rol_id, nombre, apellido, documento, email, password_hash, telefono)
            SELECT r.id, 'Ejemplo', 'Demostración', '9000000099', 'demo.pasajero@lamana.local', :hash, '0990000099'
              FROM roles r
             WHERE r.nombre = 'cliente'
               AND NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'demo.pasajero@lamana.local')
            """
        ),
        {"hash": HASH_SIN_INGRESO},
    )


async def _boletos(conexion) -> None:
    """Un pago de ejemplo por día vacío.

    El disparador impide boletos en salidas ya ocurridas, así que el viaje nace
    en el futuro, recibe el boleto y luego se corre a las 03:10 de ese día.
    """
    dias_con_pago = (
        await conexion.execute(
            text(
                """
                SELECT COUNT(DISTINCT DATE(pagado_en))
                  FROM pagos
                 WHERE estado = 'aprobado'
                   AND pagado_en >= CURDATE() - INTERVAL 29 DAY
                """
            )
        )
    ).scalar_one()
    if int(dias_con_pago or 0) >= 20:
        return
    usuario = (
        await conexion.execute(text("SELECT id FROM usuarios WHERE email = 'demo.pasajero@lamana.local'"))
    ).scalar_one_or_none()
    if usuario is None:
        return
    catalogo = (
        await conexion.execute(
            text(
                """
                SELECT r.id AS ruta_id, r.duracion_min, r.precio_base, b.id AS bus_id, MIN(a.id) AS asiento_id
                  FROM rutas r
                  JOIN buses b ON b.estado = 'operativo'
                  JOIN asientos a ON a.bus_id = b.id
                 GROUP BY r.id, r.duracion_min, r.precio_base, b.id
                 ORDER BY r.id, b.id
                """
            )
        )
    ).mappings().all()
    if not catalogo:
        return
    cubiertos = {
        fila[0]
        for fila in (
            await conexion.execute(
                text(
                    """
                    SELECT DISTINCT DATE(pagado_en)
                      FROM pagos
                     WHERE estado = 'aprobado' AND pagado_en >= CURDATE() - INTERVAL 29 DAY
                    """
                )
            )
        ).all()
    }
    hoy = ahora_colombia().date()
    ancla = (ahora_colombia() + timedelta(days=24)).replace(hour=3, minute=10, second=0, microsecond=0)
    creados = 0
    indice = 0
    for offset in range(29, -1, -1):
        dia = hoy - timedelta(days=offset)
        if dia in cubiertos:
            continue
        referencia = f"DEMO-DASH-DIA-{dia.isoformat()}"
        if (
            await conexion.execute(text("SELECT 1 FROM pagos WHERE referencia_ext = :ref"), {"ref": referencia})
        ).first():
            continue
        pieza = catalogo[indice % len(catalogo)]
        indice += 1
        salida_temp = ancla + timedelta(minutes=indice)
        llegada_temp = salida_temp + timedelta(minutes=int(pieza["duracion_min"]))
        try:
            async with conexion.begin_nested():
                viaje = await conexion.execute(
                    text(
                        """
                        INSERT INTO viajes (ruta_id, bus_id, salida, llegada_est, precio, estado)
                        VALUES (:ruta, :bus, :salida, :llegada, :precio, 'programado')
                        """
                    ),
                    {
                        "ruta": pieza["ruta_id"],
                        "bus": pieza["bus_id"],
                        "salida": salida_temp.strftime("%Y-%m-%d %H:%M:%S"),
                        "llegada": llegada_temp.strftime("%Y-%m-%d %H:%M:%S"),
                        "precio": pieza["precio_base"],
                    },
                )
                boleto = await conexion.execute(
                    text(
                        """
                        INSERT INTO boletos (
                          codigo, viaje_id, asiento_id, usuario_id, pasajero_nombre, pasajero_documento,
                          precio, estado, reservado_hasta
                        ) VALUES (
                          :codigo, :viaje, :asiento, :usuario, 'Ejemplo Demostración', '9000000099',
                          :precio, 'pagado', NULL
                        )
                        """
                    ),
                    {
                        "codigo": secrets.token_hex(6).upper(),
                        "viaje": viaje.lastrowid,
                        "asiento": pieza["asiento_id"],
                        "usuario": usuario,
                        "precio": pieza["precio_base"],
                    },
                )
                await conexion.execute(
                    text(
                        """
                        INSERT INTO pagos (boleto_id, referencia_ext, monto, metodo, proveedor, estado, pagado_en)
                        VALUES (:boleto, :ref, :monto, 'payphone', 'demo', 'aprobado', :cuando)
                        """
                    ),
                    {
                        "boleto": boleto.lastrowid,
                        "ref": referencia,
                        "monto": pieza["precio_base"],
                        "cuando": f"{dia.isoformat()} 10:15:00",
                    },
                )
                historico = f"{dia.isoformat()} 03:10:00"
                llegada_hist = (
                    datetime.fromisoformat(f"{dia.isoformat()}T03:10:00") + timedelta(minutes=int(pieza["duracion_min"]))
                ).strftime("%Y-%m-%d %H:%M:%S")
                await conexion.execute(
                    text("UPDATE viajes SET salida = :salida, llegada_est = :llegada WHERE id = :id"),
                    {"salida": historico, "llegada": llegada_hist, "id": viaje.lastrowid},
                )
            creados += 1
        except Exception as exc:
            log.warning("Pago de demostración omitido (%s): %s", referencia, exc)
    if creados:
        log.info("Pagos de demostración para el panel: %s", creados)


async def _taxis(conexion) -> None:
    columnas = (await conexion.execute(text("SHOW COLUMNS FROM taxi_viajes"))).all()
    if "ejemplo" not in {fila[0] for fila in columnas}:
        return
    existentes = (
        await conexion.execute(text("SELECT COUNT(*) FROM taxi_viajes WHERE ejemplo = 1"))
    ).scalar_one()
    if int(existentes or 0) >= 12:
        return
    recientes = (
        await conexion.execute(
            text("SELECT COUNT(*) FROM taxi_viajes WHERE creado_en >= CURDATE() - INTERVAL 1 DAY")
        )
    ).scalar_one()
    if int(recientes or 0) >= 12:
        return
    pasajero = (
        await conexion.execute(text("SELECT id FROM usuarios WHERE email = 'demo.pasajero@lamana.local'"))
    ).scalar_one_or_none()
    conductor = (
        await conexion.execute(
            text(
                """
                SELECT c.id, c.compania_id
                  FROM taxi_conductores c
                 WHERE c.activo = 1
                 ORDER BY c.ejemplo DESC, c.id
                 LIMIT 1
                """
            )
        )
    ).first()
    if pasajero is None or conductor is None:
        return
    horas = (7, 8, 9, 11, 13, 15, 17, 19)
    for dia in (1, 0):
        for indice, hora in enumerate(horas):
            await conexion.execute(
                text(
                    """
                    INSERT INTO taxi_viajes (
                      pasajero_id, compania_id, conductor_id, estado,
                      origen_lat, origen_lng, destino_lat, destino_lng, destino_texto,
                      distancia_km, duracion_min, tarifa_estimada, tarifa_final,
                      metodo_pago, pago_estado, comentario, ejemplo, creado_en
                    ) VALUES (
                      :pasajero, :compania, :conductor, 'finalizado',
                      -0.9406, -79.2344, :dlat, :dlng, 'Ejemplo: recorrido de demostración',
                      :km, :minutos, :tarifa, :tarifa,
                      'efectivo', 'no_aplica', 'Ejemplo para el gráfico del panel. No es una tarifa oficial.',
                      1, :cuando
                    )
                    """
                ),
                {
                    "pasajero": pasajero,
                    "compania": conductor[1],
                    "conductor": conductor[0],
                    "dlat": -0.9406 + (indice + 1) * 0.004,
                    "dlng": -79.2344 + (indice + 1) * 0.003,
                    "km": round(1.2 + indice * 0.35, 3),
                    "minutos": 6 + indice,
                    "tarifa": round(1.25 + indice * 0.4, 2),
                    "cuando": f"{(ahora_colombia().date() - timedelta(days=dia)).isoformat()} {hora:02d}:10:00",
                },
            )
    log.info("Viajes de taxi de demostración listos")


async def _evento(conexion) -> None:
    await conexion.execute(
        text(
            """
            INSERT INTO turismo_eventos (categoria_id, titulo, slug, resumen, cuerpo, inicio, fin, lugar)
            SELECT c.id, 'Ejemplo: feria del cacao', 'ejemplo-feria-del-cacao',
                   'Ejemplo de agenda para el panel. No es un programa oficial.',
                   'Esta ficha es de demostración. No anuncia una feria real ni un horario del municipio. Taquilla puede borrarla cuando publique la agenda de verdad.',
                   CURDATE() + INTERVAL 18 DAY, CURDATE() + INTERVAL 18 DAY, 'Ejemplo'
              FROM turismo_categorias c
             WHERE c.tipo = 'evento' AND c.slug = 'fiesta'
               AND NOT EXISTS (SELECT 1 FROM turismo_eventos WHERE slug = 'ejemplo-feria-del-cacao')
               AND NOT EXISTS (SELECT 1 FROM turismo_eventos WHERE activo = 1 AND inicio >= CURDATE())
            """
        )
    )
