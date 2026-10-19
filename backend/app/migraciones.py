"""Ajustes de esquema para bases que ya estaban creadas."""

from sqlalchemy import text

from app.database import engine


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
