from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.identificacion import CONSUMIDOR_FINAL, ruc_valido, validar_identificacion


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


class FacturacionIn(BaseModel):
    tipo: Literal["cedula", "ruc", "pasaporte", "consumidor_final"]
    identificacion: str = Field(min_length=5, max_length=20)
    razon_social: str = Field(min_length=3, max_length=300)
    direccion: str = Field(min_length=4, max_length=300)
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=30)

    @field_validator("identificacion", "razon_social", "direccion", mode="before")
    @classmethod
    def recortar(cls, valor: str) -> str:
        return str(valor or "").strip()

    @field_validator("identificacion")
    @classmethod
    def en_mayusculas(cls, valor: str) -> str:
        return valor.upper()

    @field_validator("email", mode="before")
    @classmethod
    def email_opcional(cls, valor):
        if valor is None:
            return None
        limpio = str(valor).strip()
        return limpio or None

    @field_validator("telefono")
    @classmethod
    def telefono_limpio(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpio = valor.strip()
        return limpio or None

    @model_validator(mode="before")
    @classmethod
    def fijar_consumidor_final(cls, datos):
        if isinstance(datos, dict) and datos.get("tipo") == "consumidor_final":
            datos = dict(datos)
            datos["identificacion"] = CONSUMIDOR_FINAL
            datos["razon_social"] = "CONSUMIDOR FINAL"
        return datos

    @model_validator(mode="after")
    def identificacion_oficial(self):
        mensaje = validar_identificacion(self.tipo, self.identificacion)
        if mensaje:
            raise ValueError(mensaje)
        return self


class PagarIn(BaseModel):
    referencia_ext: str = Field(min_length=4, max_length=64)
    metodo: Literal["deuna", "tarjeta", "payphone"]
    ultimos4: str | None = Field(default=None, max_length=4)
    facturacion: FacturacionIn

    @field_validator("referencia_ext")
    @classmethod
    def sin_bordes(cls, valor: str) -> str:
        return valor.strip()


class PortadaIn(BaseModel):
    titulo: str = Field(min_length=3, max_length=160)
    subtitulo: str = ""
    texto_boton: str = ""
    enlace_boton: str = ""
    enlace: str | None = None
    orden: int = 0
    activo: bool = True
    ambito: Literal["portal", "transporte"] | None = None


class TurismoCategoriaIn(BaseModel):
    tipo: Literal["atractivo", "gastronomia", "hospedaje", "actividad", "ruta", "parroquia", "guia", "evento"]
    nombre: str = Field(min_length=3, max_length=120)
    resumen: str = ""
    orden: int = 0
    activo: bool = True


class TurismoFichaIn(BaseModel):
    tipo: Literal["atractivo", "gastronomia", "hospedaje", "actividad", "ruta", "parroquia", "guia"]
    categoria_id: int | None = None
    nombre: str = Field(min_length=3, max_length=160)
    resumen: str = Field(min_length=3, max_length=400)
    cuerpo: str = Field(min_length=3, max_length=8000)
    zona: str = ""
    direccion: str = ""
    lat: float | None = None
    lng: float | None = None
    imagen: str | None = None
    credito: str = ""
    destacado: bool = False
    orden: int = 0
    activo: bool = True


class TurismoEventoIn(BaseModel):
    categoria_id: int | None = None
    titulo: str = Field(min_length=3, max_length=160)
    resumen: str = Field(min_length=3, max_length=400)
    cuerpo: str = Field(min_length=3, max_length=8000)
    inicio: date
    fin: date | None = None
    lugar: str = ""
    imagen: str | None = None
    credito: str = ""
    activo: bool = True


class TurismoContactoIn(BaseModel):
    nombre: str = Field(min_length=3, max_length=120)
    email: EmailStr
    mensaje: str = Field(min_length=8, max_length=1000)


class EmisorIn(BaseModel):
    ruc: str = Field(min_length=13, max_length=13)
    razon_social: str = Field(min_length=3, max_length=300)
    nombre_comercial: str = Field(min_length=3, max_length=300)
    establecimiento: str = Field(min_length=1, max_length=3)
    punto_emision: str = Field(min_length=1, max_length=3)
    direccion_matriz: str = Field(min_length=4, max_length=300)
    obligado_contabilidad: bool = True
    ambiente: Literal["pruebas", "produccion"] = "pruebas"
    tarifa_iva_pasaje: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)

    @field_validator("ruc", "razon_social", "nombre_comercial", "direccion_matriz", mode="before")
    @classmethod
    def recortar(cls, valor: str) -> str:
        return str(valor or "").strip()

    @field_validator("establecimiento", "punto_emision")
    @classmethod
    def tres_digitos(cls, valor: str) -> str:
        limpio = str(valor).strip()
        if not limpio.isdigit():
            raise ValueError("Establecimiento y punto de emisión usan solo dígitos")
        return f"{int(limpio):03d}"

    @model_validator(mode="after")
    def ruc_oficial(self):
        if not ruc_valido(self.ruc):
            raise ValueError("El RUC del emisor no supera la validación de sociedad o persona natural")
        return self


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


class CiudadIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    departamento: str = Field(min_length=2, max_length=120)

    @field_validator("nombre", "departamento")
    @classmethod
    def sin_bordes(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("El campo es demasiado corto")
        return limpio


class RutaIn(BaseModel):
    origen_id: int = Field(gt=0)
    destino_id: int = Field(gt=0)
    duracion_min: int = Field(gt=0, le=1440)
    precio_base: Decimal = Field(gt=0, max_digits=10, decimal_places=2)

    @model_validator(mode="after")
    def distintas(self):
        if self.origen_id == self.destino_id:
            raise ValueError("El origen y el destino deben ser distintos")
        return self


class BusIn(BaseModel):
    placa: str = Field(min_length=4, max_length=10)
    numero_disco: str = Field(min_length=1, max_length=10)
    pisos: int = Field(ge=1, le=2)
    filas: int = Field(ge=1, le=20)
    estado: Literal["operativo", "mantenimiento", "inactivo"] = "operativo"

    @field_validator("placa", "numero_disco")
    @classmethod
    def sin_bordes(cls, valor: str) -> str:
        return valor.strip().upper()

    @model_validator(mode="after")
    def cupo(self):
        if self.pisos * self.filas * 4 > 100:
            raise ValueError("El bus no puede tener más de 100 asientos")
        return self


class BusEstadoIn(BaseModel):
    estado: Literal["operativo", "mantenimiento", "inactivo"]


class AnuncioIn(BaseModel):
    titulo: str = Field(min_length=3, max_length=140)
    mensaje: str = Field(default="", max_length=500)
    enlace: str | None = Field(default=None, max_length=255)
    texto_boton: str | None = Field(default=None, max_length=80)
    tipo: Literal["banner", "modal"] = "modal"
    formato: Literal["texto", "imagen"] = "texto"
    activo: bool = True
    inicio: date
    fin: date

    @field_validator("titulo", "mensaje")
    @classmethod
    def sin_bordes(cls, valor: str) -> str:
        return (valor or "").strip()

    @field_validator("enlace", "texto_boton", mode="before")
    @classmethod
    def opcional(cls, valor):
        if valor is None:
            return None
        limpio = str(valor).strip()
        return limpio or None

    @field_validator("activo", mode="before")
    @classmethod
    def a_bool(cls, valor):
        if isinstance(valor, bool):
            return valor
        return str(valor).strip().lower() in {"1", "true", "on", "si", "sí"}

    @model_validator(mode="after")
    def reglas(self):
        if self.fin < self.inicio:
            raise ValueError("La fecha final no puede ser anterior al inicio")
        if self.formato == "texto" and len(self.mensaje) < 8:
            raise ValueError("El mensaje debe tener al menos 8 caracteres")
        return self


class ViajeIn(BaseModel):
    ruta_id: int = Field(gt=0)
    bus_id: int = Field(gt=0)
    salida: datetime
    precio: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)


class TarifaIn(BaseModel):
    precio_base: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
