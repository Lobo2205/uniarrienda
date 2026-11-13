"""Configuración leída del archivo .env (nunca se sube a GitHub)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/uniarrienda"
    jwt_secret: str = "solo-para-desarrollo-cambiar"
    jwt_minutos: int = 1440
    carpeta_media: str = "media"
    url_publica: str = "http://localhost:8000"

    # Stripe (modo prueba). Si está vacío, se usa la pasarela falsa.
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_url_exito: str = "http://localhost:8000/pagos/exito"
    stripe_url_cancelar: str = "http://localhost:8000/pagos/cancelado"


@lru_cache
def obtener_config() -> Configuracion:
    return Configuracion()
