from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SesionLocal
from app.modelos import Rol, Usuario
from app.seguridad import JWTError, decodificar_token

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def obtener_sesion():
    async with SesionLocal() as sesion:
        yield sesion


async def usuario_actual(
    token: str = Depends(oauth2),
    sesion: AsyncSession = Depends(obtener_sesion),
) -> dict:
    credenciales = HTTPException(
        status_code=401,
        detail="Sesión inválida o expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decodificar_token(token)
        usuario_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise credenciales
    resultado = await sesion.execute(
        select(Usuario, Rol.nombre)
        .join(Rol, Rol.id == Usuario.rol_id)
        .where(Usuario.id == usuario_id)
    )
    fila = resultado.first()
    if fila is None or not fila[0].activo:
        raise credenciales
    usuario, rol = fila
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "email": usuario.email,
        "documento": usuario.documento,
        "rol": rol,
    }


async def exigir_admin(usuario: dict = Depends(usuario_actual)) -> dict:
    if usuario["rol"] != "administrador":
        raise HTTPException(status_code=403, detail="Se requiere rol administrador")
    return usuario


def exigir_roles(*roles: str):
    permitidos = set(roles)

    async def dependencia(usuario: dict = Depends(usuario_actual)) -> dict:
        if usuario["rol"] not in permitidos:
            raise HTTPException(status_code=403, detail="No tienes permiso para este módulo")
        return usuario

    return dependencia


exigir_turismo = exigir_roles("administrador", "operador_turismo")
exigir_transporte = exigir_roles("administrador", "operador_transporte")
exigir_taxi = exigir_roles("administrador", "operador_taxi")
exigir_portada = exigir_roles("administrador", "operador_turismo", "operador_transporte")
exigir_panel = exigir_roles("administrador", "operador_turismo", "operador_transporte", "operador_taxi")
exigir_pasajero = exigir_roles("administrador", "cliente", "operador_turismo", "operador_transporte", "operador_taxi", "conductor")
