from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError


class CodigoDuplicado(Exception):
    """El código aleatorio del boleto chocó con uk_boleto_codigo."""


def codigo_mysql(exc: Exception) -> tuple[int | None, str]:
    orig = getattr(exc, "orig", None)
    args = getattr(orig, "args", ()) or ()
    if not args or not isinstance(args[0], int):
        return None, str(exc)
    texto = str(args[1]) if len(args) > 1 else str(orig)
    return args[0], texto


def traducir_error_mysql(exc: SQLAlchemyError) -> None:
    numero, texto = codigo_mysql(exc)
    if numero == 1062:
        if "uk_boleto_codigo" in texto:
            raise CodigoDuplicado() from exc
        if "uk_boleto_asiento" in texto or "ocupa_asiento" in texto:
            raise HTTPException(status_code=409, detail="Asiento no disponible") from exc
        if "uk_pago_ref" in texto or "referencia_ext" in texto:
            raise HTTPException(status_code=409, detail="La referencia de pago ya fue registrada") from exc
        if "uk_pago_boleto" in texto:
            raise HTTPException(status_code=409, detail="El boleto ya tiene un pago registrado") from exc
        if "uk_usuarios_email" in texto:
            raise HTTPException(status_code=409, detail="El correo ya está registrado") from exc
        if "uk_usuarios_documento" in texto:
            raise HTTPException(status_code=409, detail="El documento ya está registrado") from exc
        raise HTTPException(status_code=409, detail="Registro duplicado") from exc
    if numero == 1644:
        raise HTTPException(status_code=422, detail=texto) from exc
    if numero == 1452:
        raise HTTPException(status_code=422, detail="Viaje, asiento o usuario inexistente") from exc
    if numero == 3819:
        raise HTTPException(status_code=422, detail="Los datos no cumplen las reglas del sistema") from exc
    raise exc
