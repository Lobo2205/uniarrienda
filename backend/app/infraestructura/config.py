"""Configuración leída del archivo .env (nunca se sube a GitHub)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/uniarrienda"
    jwt_secret: str = "solo-para-desarrollo-cambiar"
    jwt_minutos: int = 1440
    carpeta_media: str = "media"           # donde se guardan las fotos subidas
    url_publica: str = "http://localhost:8000"  # para armar la URL de las fotos


@lru_cache
def obtener_config() -> Configuracion:
    return Configuracion()
