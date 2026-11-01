"""Textos del sitio que el panel puede cambiar y las páginas públicas leen."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencias import exigir_panel, obtener_sesion

router = APIRouter()

ESPACIOS = {"portal", "transporte", "taxi", "sitio"}


def _puede(rol: str, espacio: str) -> bool:
    if rol == "administrador":
        return True
    return {
        "operador_turismo": espacio in {"portal", "sitio"},
        "operador_transporte": espacio == "transporte",
        "operador_taxi": espacio == "taxi",
    }.get(rol, False)


def _fila(fila) -> dict:
    return {
        "id": int(fila["id"]),
        "espacio": fila["espacio"],
        "clave": fila["clave"],
        "etiqueta": fila["etiqueta"],
        "ayuda": fila["ayuda"],
        "aparece": fila["aparece"],
        "valor": fila["valor"],
        "maximo": int(fila["maximo"]),
        "orden": int(fila["orden"]),
    }


@router.get("/textos")
async def textos_publicos(espacio: str = Query(...), sesion: AsyncSession = Depends(obtener_sesion)):
    if espacio not in ESPACIOS:
        raise HTTPException(status_code=422, detail="Ese espacio no existe")
    filas = (
        await sesion.execute(
            text("SELECT clave, valor FROM sitio_textos WHERE espacio = :espacio ORDER BY orden, clave"),
            {"espacio": espacio},
        )
    ).mappings().all()
    return {fila["clave"]: fila["valor"] for fila in filas}


@router.get("/admin/textos")
async def textos_admin(
    espacio: str | None = None,
    usuario: dict = Depends(exigir_panel),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    if espacio is not None and espacio not in ESPACIOS:
        raise HTTPException(status_code=422, detail="Ese espacio no existe")
    if espacio is not None and not _puede(usuario["rol"], espacio):
        raise HTTPException(status_code=403, detail="No puedes editar este espacio")
    sql = "SELECT * FROM sitio_textos"
    params: dict = {}
    if espacio is not None:
        sql += " WHERE espacio = :espacio"
        params["espacio"] = espacio
    elif usuario["rol"] != "administrador":
        permitidos = [item for item in ESPACIOS if _puede(usuario["rol"], item)]
        if not permitidos:
            return []
        marcas = ", ".join(f":e{i}" for i in range(len(permitidos)))
        sql += f" WHERE espacio IN ({marcas})"
        params = {f"e{i}": valor for i, valor in enumerate(permitidos)}
    sql += " ORDER BY espacio, orden, clave"
    filas = (await sesion.execute(text(sql), params)).mappings().all()
    return [_fila(fila) for fila in filas]


@router.patch("/admin/textos/{texto_id}")
async def actualizar_texto(
    texto_id: int,
    cuerpo: dict,
    usuario: dict = Depends(exigir_panel),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    fila = (
        await sesion.execute(text("SELECT * FROM sitio_textos WHERE id = :id"), {"id": texto_id})
    ).mappings().first()
    if fila is None:
        raise HTTPException(status_code=404, detail="No encontramos ese texto")
    if not _puede(usuario["rol"], fila["espacio"]):
        raise HTTPException(status_code=403, detail="No puedes editar este espacio")
    if "valor" not in cuerpo:
        raise HTTPException(status_code=422, detail="Escribe el texto nuevo en valor")
    valor = str(cuerpo["valor"]).strip()
    if not valor:
        raise HTTPException(status_code=422, detail="El texto no puede quedar vacío")
    if len(valor) > int(fila["maximo"]):
        raise HTTPException(
            status_code=422,
            detail=f"Máximo {fila['maximo']} caracteres. Ahora tiene {len(valor)}.",
        )
    await sesion.execute(
        text("UPDATE sitio_textos SET valor = :valor WHERE id = :id"),
        {"valor": valor, "id": texto_id},
    )
    await sesion.commit()
    fresco = (
        await sesion.execute(text("SELECT * FROM sitio_textos WHERE id = :id"), {"id": texto_id})
    ).mappings().one()
    return _fila(fresco)
