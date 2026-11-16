import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hashear_password(password: str) -> str:
    return _pwd.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    return _pwd.verify(password, password_hash)


def crear_access_token(usuario_id: int, rol: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutos)
    return jwt.encode(
        {"sub": str(usuario_id), "rol": rol, "exp": expira},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decodificar_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def nuevo_refresh_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(48)
    digest = hashlib.sha256(token.encode()).hexdigest()
    return token, digest


def hash_refresh(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


__all__ = [
    "JWTError",
    "crear_access_token",
    "decodificar_token",
    "hash_refresh",
    "hashear_password",
    "nuevo_refresh_token",
    "verificar_password",
]
