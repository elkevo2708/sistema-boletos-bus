from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "mysql+aiomysql://boletos:boletos@mysql:3306/boletos?charset=utf8mb4"
    jwt_secret: str = "viaandina-dev-secreto-cambiar"
    jwt_algorithm: str = "HS256"
    access_token_minutos: int = 60
    refresh_token_dias: int = 7
    cors_origins: str = "http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173"

    @property
    def origenes_cors(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origins.split(",") if origen.strip()]


settings = Configuracion()
