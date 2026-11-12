"""Tablas de PostgreSQL. Son detalles técnicos: el dominio no las conoce."""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infraestructura.base_datos import Base


class UsuarioORM(Base):
    __tablename__ = "usuarios"
    id_usuario: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    correo: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    contrasena: Mapped[str] = mapped_column(String(200))
    telefono: Mapped[str] = mapped_column(String(30))
    rol: Mapped[str] = mapped_column(String(20))
    universidad: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)


class InmuebleORM(Base):
    __tablename__ = "inmuebles"
    id_inmueble: Mapped[int] = mapped_column(primary_key=True)
    arrendador_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id_usuario"), index=True)
    titulo: Mapped[str] = mapped_column(String(160))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    precio: Mapped[int] = mapped_column(Integer)
    tipo: Mapped[str] = mapped_column(String(20))
    disponibilidad: Mapped[bool] = mapped_column(Boolean, default=True)
    estado: Mapped[str] = mapped_column(String(20), default="publicado")
    fecha_publicacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    # Especificaciones (decisión A)
    habitaciones: Mapped[int] = mapped_column(Integer, default=1)
    banos: Mapped[int] = mapped_column(Integer, default=1)
    cocina: Mapped[bool] = mapped_column(Boolean, default=False)
    estacionamiento: Mapped[bool] = mapped_column(Boolean, default=False)
    mascotas: Mapped[bool] = mapped_column(Boolean, default=False)
    wifi: Mapped[bool] = mapped_column(Boolean, default=False)
    servicios_incluidos: Mapped[bool] = mapped_column(Boolean, default=False)

    ubicacion: Mapped["UbicacionORM"] = relationship(cascade="all, delete-orphan", uselist=False, lazy="joined")
    fotografias: Mapped[List["FotografiaORM"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    requisitos: Mapped[List["RequisitoORM"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class UbicacionORM(Base):
    __tablename__ = "ubicaciones"
    id_ubicacion: Mapped[int] = mapped_column(primary_key=True)
    inmueble_id: Mapped[int] = mapped_column(ForeignKey("inmuebles.id_inmueble", ondelete="CASCADE"), unique=True)
    direccion: Mapped[str] = mapped_column(String(200))
    barrio: Mapped[str] = mapped_column(String(120), index=True)
    latitud: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitud: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class FotografiaORM(Base):
    __tablename__ = "fotografias"
    id_fotografia: Mapped[int] = mapped_column(primary_key=True)
    inmueble_id: Mapped[int] = mapped_column(ForeignKey("inmuebles.id_inmueble", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(String(500))
    espacio: Mapped[str] = mapped_column(String(60))


class RequisitoORM(Base):
    __tablename__ = "requisitos"
    id_requisito: Mapped[int] = mapped_column(primary_key=True)
    inmueble_id: Mapped[int] = mapped_column(ForeignKey("inmuebles.id_inmueble", ondelete="CASCADE"))
    descripcion: Mapped[str] = mapped_column(String(300))
