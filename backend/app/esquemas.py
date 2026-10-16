from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegistroIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    apellido: str = Field(min_length=1, max_length=120)
    documento: str = Field(min_length=5, max_length=20)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    telefono: str | None = Field(default=None, max_length=30)

    @field_validator("nombre", "apellido", "documento")
    @classmethod
    def sin_bordes(cls, valor: str) -> str:
        limpio = valor.strip()
        if not limpio:
            raise ValueError("El campo no puede estar vacío")
        return limpio

    @field_validator("email")
    @classmethod
    def correo_minuscula(cls, valor: str) -> str:
        return valor.strip().lower()

    @field_validator("telefono")
    @classmethod
    def telefono_limpio(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpio = valor.strip()
        return limpio or None


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=200)


class ReservarIn(BaseModel):
    viaje_id: int = Field(gt=0)
    asiento_id: int = Field(gt=0)
    pasajero_nombre: str = Field(min_length=3, max_length=180)
    pasajero_documento: str = Field(min_length=5, max_length=20)

    @field_validator("pasajero_nombre", "pasajero_documento")
    @classmethod
    def sin_bordes(cls, valor: str) -> str:
        return valor.strip()


class PagarIn(BaseModel):
    referencia_ext: str = Field(min_length=4, max_length=64)
    metodo: Literal["tarjeta", "transferencia", "payphone", "efectivo"] = "efectivo"

    @field_validator("referencia_ext")
    @classmethod
    def sin_bordes(cls, valor: str) -> str:
        return valor.strip()


class BlogIn(BaseModel):
    titulo: str = Field(min_length=4, max_length=180)
    resumen: str = Field(min_length=10, max_length=400)
    cuerpo: str = Field(min_length=20, max_length=20000)
    categoria: Literal["noticia", "destino"]
    imagen: str | None = Field(default=None, max_length=255)
    publicado: bool = True
    publicado_en: datetime

    @field_validator("titulo", "resumen", "cuerpo")
    @classmethod
    def sin_bordes(cls, valor: str) -> str:
        return valor.strip()

    @field_validator("imagen")
    @classmethod
    def imagen_limpia(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpio = valor.strip().lstrip("/")
        if limpio.startswith("medios/"):
            limpio = limpio[len("medios/") :]
        return limpio or None


class AnuncioIn(BaseModel):
    titulo: str = Field(min_length=3, max_length=140)
    mensaje: str = Field(min_length=8, max_length=500)
    enlace: str | None = Field(default=None, max_length=255)
    tipo: Literal["banner", "modal"] = "banner"
    activo: bool = True
    inicio: date
    fin: date

    @field_validator("titulo", "mensaje")
    @classmethod
    def sin_bordes(cls, valor: str) -> str:
        return valor.strip()

    @field_validator("enlace")
    @classmethod
    def enlace_limpio(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpio = valor.strip()
        return limpio or None


class ViajeIn(BaseModel):
    ruta_id: int = Field(gt=0)
    bus_id: int = Field(gt=0)
    salida: datetime
    precio: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)


class TarifaIn(BaseModel):
    precio_base: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
