"""Ajustes de esquema para bases que ya estaban creadas."""

from pathlib import Path

from sqlalchemy import text

from app.database import engine

SQL_PAGOS = Path(__file__).parent / "sql" / "migracion_pagos_portada.sql"


async def _ejecutar(sql: str) -> None:
    async with engine.begin() as conexion:
        await conexion.execute(text(sql))


async def asegurar_esquema() -> None:
    async with engine.connect() as conexion:
        filas = (await conexion.execute(text("SHOW COLUMNS FROM anuncios"))).all()
    nombres = {fila[0] for fila in filas}
    if "texto_boton" not in nombres:
        await _ejecutar("ALTER TABLE anuncios ADD COLUMN texto_boton VARCHAR(80) NULL AFTER enlace")
    if "formato" not in nombres:
        await _ejecutar(
            "ALTER TABLE anuncios ADD COLUMN formato ENUM('texto', 'imagen') NOT NULL DEFAULT 'texto' AFTER texto_boton"
        )
    if "imagen" not in nombres:
        await _ejecutar("ALTER TABLE anuncios ADD COLUMN imagen VARCHAR(255) NULL AFTER formato")
    await _ejecutar("ALTER TABLE anuncios MODIFY mensaje VARCHAR(500) NULL")
    await _aplicar_archivo(SQL_PAGOS)


def _sentencias(contenido: str) -> list[str]:
    lineas = []
    for linea in contenido.splitlines():
        if linea.strip().startswith("--"):
            continue
        lineas.append(linea)
    return [parte.strip() for parte in "\n".join(lineas).split(";") if parte.strip()]


async def _aplicar_archivo(ruta: Path) -> None:
    for sentencia in _sentencias(ruta.read_text(encoding="utf-8")):
        await _ejecutar(sentencia)
