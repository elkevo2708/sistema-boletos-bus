"""Aplica el horario recurrente y completa los próximos 30 días de salidas."""

from pathlib import Path

from sqlalchemy import text

from app.database import engine

SQL = Path(__file__).parent / "sql" / "migracion_horarios.sql"


def _sentencias(contenido: str) -> list[str]:
    lineas = []
    for linea in contenido.splitlines():
        if linea.strip().startswith("--"):
            continue
        lineas.append(linea)
    return [parte.strip() for parte in "\n".join(lineas).split(";") if parte.strip()]


async def generar_salidas() -> int:
    sentencias = _sentencias(SQL.read_text(encoding="utf-8"))
    creados = 0
    for indice, sentencia in enumerate(sentencias):
        async with engine.begin() as conexion:
            resultado = await conexion.execute(text(sentencia))
            if indice == len(sentencias) - 1:
                creados = int(resultado.rowcount or 0)
    return max(creados, 0)
