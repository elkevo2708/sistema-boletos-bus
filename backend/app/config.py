from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "mysql+aiomysql://boletos:boletos@mysql:3306/boletos?charset=utf8mb4"
    jwt_secret: str = "viaandina-dev-secreto-cambiar"
    jwt_algorithm: str = "HS256"
    access_token_minutos: int = 60
    refresh_token_dias: int = 7
    cors_origins: str = "http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173"
    identificacion_lookup_url: str = ""
    identificacion_lookup_api_key: str = ""
    identificacion_lookup_header: str = "Authorization"
    identificacion_lookup_scheme: str = "Bearer"
    identificacion_lookup_metodo: str = "GET"
    identificacion_lookup_campo_nombre: str = "nombres,apellidos"
    identificacion_lookup_campo_direccion: str = "direccion"
    identificacion_lookup_campo_email: str = "email"
    identificacion_lookup_campo_telefono: str = "telefono"
    pagos_modo: str = "sandbox"
    pagos_webhook_secreto: str = ""
    public_base_url: str = "http://localhost:8080"
    payphone_token: str = ""
    payphone_store_id: str = ""
    payphone_api_url: str = "https://pay.payphonetodoesposible.com/api/button"
    deuna_api_key: str = ""
    deuna_api_secret: str = ""
    deuna_api_url: str = "https://api.sandbox.deuna.io"
    deuna_point_of_sale: str = ""
    tarjeta_proveedor: str = "payphone"
    tarjeta_api_url: str = ""
    tarjeta_api_key: str = ""
    firma_p12_ruta: str = ""
    firma_p12_clave: str = ""
    sri_modo: str = "offline"
    sri_recepcion_url: str = ""
    sri_autorizacion_url: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_usuario: str = ""
    smtp_clave: str = ""
    smtp_desde: str = "facturacion@lamana.ec"

    @property
    def origenes_cors(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origins.split(",") if origen.strip()]


settings = Configuracion()
