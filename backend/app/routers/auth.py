from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencias import obtener_sesion, usuario_actual
from app.errores import traducir_error_mysql
from app.esquemas import RefreshIn, RegistroIn
from app.modelos import RefreshToken, Rol, Usuario
from app.seguridad import (
    crear_access_token,
    hash_refresh,
    hashear_password,
    nuevo_refresh_token,
    verificar_password,
)
from app.tiempo import ahora_colombia

router = APIRouter()


def _respuesta_sesion(usuario: Usuario, rol: str, refresh: str) -> dict:
    return {
        "access_token": crear_access_token(usuario.id, rol),
        "refresh_token": refresh,
        "token_type": "bearer",
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "email": usuario.email,
            "documento": usuario.documento,
            "rol": rol,
        },
    }


async def _emitir_refresh(sesion: AsyncSession, usuario_id: int) -> str:
    token, digest = nuevo_refresh_token()
    sesion.add(
        RefreshToken(
            usuario_id=usuario_id,
            token_hash=digest,
            expira_en=ahora_colombia() + timedelta(days=settings.refresh_token_dias),
            revocado=False,
        )
    )
    return token


@router.post("/registro", status_code=201)
async def registro(datos: RegistroIn, sesion: AsyncSession = Depends(obtener_sesion)):
    rol = (
        await sesion.execute(select(Rol).where(Rol.nombre == "cliente"))
    ).scalar_one_or_none()
    if rol is None:
        raise HTTPException(status_code=500, detail="El rol cliente no está configurado")
    usuario = Usuario(
        rol_id=rol.id,
        nombre=datos.nombre,
        apellido=datos.apellido,
        documento=datos.documento,
        email=datos.email,
        password_hash=hashear_password(datos.password),
        telefono=datos.telefono,
        activo=True,
    )
    sesion.add(usuario)
    try:
        await sesion.flush()
        refresh = await _emitir_refresh(sesion, usuario.id)
        await sesion.commit()
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)
    await sesion.refresh(usuario)
    return _respuesta_sesion(usuario, "cliente", refresh)


@router.post("/login")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    sesion: AsyncSession = Depends(obtener_sesion),
):
    email = form.username.strip().lower()
    resultado = await sesion.execute(
        select(Usuario, Rol.nombre).join(Rol, Rol.id == Usuario.rol_id).where(Usuario.email == email)
    )
    fila = resultado.first()
    if fila is None or not fila[0].activo or not verificar_password(form.password, fila[0].password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    usuario, rol = fila
    try:
        refresh = await _emitir_refresh(sesion, usuario.id)
        await sesion.commit()
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)
    return _respuesta_sesion(usuario, rol, refresh)


@router.post("/refresh")
async def refrescar(datos: RefreshIn, sesion: AsyncSession = Depends(obtener_sesion)):
    digest = hash_refresh(datos.refresh_token)
    guardado = (
        await sesion.execute(select(RefreshToken).where(RefreshToken.token_hash == digest))
    ).scalar_one_or_none()
    ahora = ahora_colombia()
    if guardado is None or guardado.revocado or guardado.expira_en <= ahora:
        raise HTTPException(status_code=401, detail="El refresh token no es válido")
    resultado = await sesion.execute(
        select(Usuario, Rol.nombre).join(Rol, Rol.id == Usuario.rol_id).where(Usuario.id == guardado.usuario_id)
    )
    fila = resultado.first()
    if fila is None or not fila[0].activo:
        raise HTTPException(status_code=401, detail="El refresh token no es válido")
    usuario, rol = fila
    guardado.revocado = True
    guardado.revocado_en = ahora
    try:
        refresh = await _emitir_refresh(sesion, usuario.id)
        await sesion.commit()
    except SQLAlchemyError as exc:
        await sesion.rollback()
        traducir_error_mysql(exc)
    return _respuesta_sesion(usuario, rol, refresh)


@router.post("/logout", status_code=204)
async def logout(datos: RefreshIn, sesion: AsyncSession = Depends(obtener_sesion)):
    digest = hash_refresh(datos.refresh_token)
    guardado = (
        await sesion.execute(select(RefreshToken).where(RefreshToken.token_hash == digest))
    ).scalar_one_or_none()
    if guardado is not None and not guardado.revocado:
        guardado.revocado = True
        guardado.revocado_en = ahora_colombia()
        await sesion.commit()


@router.get("/yo")
async def yo(usuario: dict = Depends(usuario_actual)):
    return usuario
