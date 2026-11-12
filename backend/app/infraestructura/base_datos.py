"""Conexión a la base de datos con SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import obtener_config


class Base(DeclarativeBase):
    pass


motor = create_engine(obtener_config().database_url, pool_pre_ping=True)
FabricaSesiones = sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)


def crear_tablas() -> None:
    # Importar los modelos para que SQLAlchemy los registre antes de crear las tablas
    from app.adaptadores.salida import modelos_orm  # noqa: F401
    Base.metadata.create_all(motor)
