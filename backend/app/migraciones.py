"""Ajustes de esquema para bases que ya estaban creadas."""

from pathlib import Path

from sqlalchemy import text

from app.database import engine

SQL_PAGOS = Path(__file__).parent / "sql" / "migracion_pagos_portada.sql"
SQL_TURISMO = Path(__file__).parent / "sql" / "migracion_turismo.sql"
SQL_PORTAL_TAXI = Path(__file__).parent / "sql" / "migracion_portal_taxi.sql"


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
    await _ambito_portada()
    await _aplicar_archivo(SQL_TURISMO)
    await _aplicar_archivo(SQL_PORTAL_TAXI)
    await _ejemplo_taxi()


def _sentencias(contenido: str) -> list[str]:
    """Parte el archivo por `;` fuera de textos. Un punto y coma dentro de una ficha no corta la sentencia."""
    lineas = []
    for linea in contenido.splitlines():
        if linea.strip().startswith("--"):
            continue
        lineas.append(linea)
    texto = "\n".join(lineas)
    partes: list[str] = []
    actual: list[str] = []
    en_texto = False
    indice = 0
    while indice < len(texto):
        caracter = texto[indice]
        if en_texto:
            actual.append(caracter)
            if caracter == "\\" and indice + 1 < len(texto):
                actual.append(texto[indice + 1])
                indice += 2
                continue
            if caracter == "'":
                if indice + 1 < len(texto) and texto[indice + 1] == "'":
                    actual.append("'")
                    indice += 2
                    continue
                en_texto = False
            indice += 1
            continue
        if caracter == "'":
            en_texto = True
            actual.append(caracter)
            indice += 1
            continue
        if caracter == ";":
            sentencia = "".join(actual).strip()
            if sentencia:
                partes.append(sentencia)
            actual = []
            indice += 1
            continue
        actual.append(caracter)
        indice += 1
    resto = "".join(actual).strip()
    if resto:
        partes.append(resto)
    return partes


async def _ambito_portada() -> None:
    async with engine.connect() as conexion:
        columnas = (await conexion.execute(text("SHOW COLUMNS FROM portada"))).all()
    if "ambito" not in {fila[0] for fila in columnas}:
        await _ejecutar(
            "ALTER TABLE portada ADD COLUMN ambito ENUM('portal', 'transporte') NOT NULL DEFAULT 'portal' AFTER activo"
        )
    await _ejecutar(
        """
        UPDATE portada
           SET ambito = 'transporte'
         WHERE enlace = '/bus-lamana.jpg'
            OR titulo LIKE '%asiento ya elegido%'
            OR titulo LIKE '%unidad naranja%'
        """
    )


async def _ejemplo_taxi() -> None:
    async with engine.connect() as conexion:
        tablas = (await conexion.execute(text("SHOW TABLES LIKE 'taxi_viajes'"))).first()
        if tablas is None:
            return
        columnas = (await conexion.execute(text("SHOW COLUMNS FROM taxi_viajes"))).all()
    if "ejemplo" not in {fila[0] for fila in columnas}:
        await _ejecutar("ALTER TABLE taxi_viajes ADD COLUMN ejemplo TINYINT(1) NOT NULL DEFAULT 0 AFTER comentario")


async def _aplicar_archivo(ruta: Path) -> None:
    for sentencia in _sentencias(ruta.read_text(encoding="utf-8")):
        await _ejecutar(sentencia)
