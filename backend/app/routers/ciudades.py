from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencias import obtener_sesion

router = APIRouter()


@router.get("")
async def listar_ciudades(sesion: AsyncSession = Depends(obtener_sesion)):
    filas = (
        await sesion.execute(
            text(
                """
                SELECT id, nombre, departamento
                  FROM ciudades
                 ORDER BY nombre
                """
            )
        )
    ).mappings().all()
    return [dict(fila) for fila in filas]
