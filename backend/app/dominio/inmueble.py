"""Entidad Inmueble y sus partes (Ubicacion, Fotografia, Requisito) del modelo V7.

Incluye la decisión A: especificaciones como atributos y barrio en Ubicacion.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from .errores import ErrorDominio, NoAutorizado


class TipoInmueble(str, Enum):
    HABITACION = "habitacion"
    APARTAMENTO = "apartamento"
    APARTAESTUDIO = "apartaestudio"
    CASA = "casa"


class EstadoInmueble(str, Enum):
    PUBLICADO = "publicado"
    ELIMINADO = "eliminado"


@dataclass
class Ubicacion:
    direccion: str
    barrio: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.direccion.strip():
            raise ErrorDominio("La dirección es obligatoria")
        if not self.barrio.strip():
            raise ErrorDominio("El barrio es obligatorio")


@dataclass
class Fotografia:
    url: str
    espacio: str  # sala, habitación, baño...


@dataclass
class Requisito:
    descripcion: str


@dataclass
class Especificaciones:
    habitaciones: int = 1
    banos: int = 1
    cocina: bool = False
    estacionamiento: bool = False
    mascotas: bool = False
    wifi: bool = False
    servicios_incluidos: bool = False

    def __post_init__(self) -> None:
        if self.habitaciones < 0 or self.banos < 0:
            raise ErrorDominio("Habitaciones y baños no pueden ser negativos")


@dataclass
class Inmueble:
    arrendador_id: int
    titulo: str
    descripcion: str
    precio: int  # pesos colombianos por mes
    tipo: TipoInmueble
    ubicacion: Ubicacion
    especificaciones: Especificaciones = field(default_factory=Especificaciones)
    fotografias: List[Fotografia] = field(default_factory=list)
    requisitos: List[Requisito] = field(default_factory=list)
    disponibilidad: bool = True
    estado: EstadoInmueble = EstadoInmueble.PUBLICADO
    fecha_publicacion: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id_inmueble: Optional[int] = None

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        if not self.titulo.strip():
            raise ErrorDominio("El título es obligatorio")
        if self.precio <= 0:
            raise ErrorDominio("El precio debe ser mayor que cero")
        if not self.fotografias:
            raise ErrorDominio("El inmueble debe tener al menos una fotografía")

    def es_de(self, usuario_id: int) -> bool:
        return self.arrendador_id == usuario_id

    def verificar_dueno(self, usuario_id: int) -> None:
        if not self.es_de(usuario_id):
            raise NoAutorizado("Solo el arrendador dueño puede modificar este inmueble")

    def actualizar_disponibilidad(self, disponible: bool) -> None:
        if self.estado == EstadoInmueble.ELIMINADO:
            raise ErrorDominio("El inmueble fue eliminado")
        self.disponibilidad = disponible

    def actualizar(self, titulo: str, descripcion: str, precio: int, tipo: "TipoInmueble",
                   ubicacion: "Ubicacion", especificaciones: "Especificaciones",
                   fotografias: List["Fotografia"], requisitos: List["Requisito"]) -> None:
        self.titulo, self.descripcion, self.precio, self.tipo = titulo, descripcion, precio, tipo
        self.ubicacion, self.especificaciones = ubicacion, especificaciones
        self.fotografias, self.requisitos = fotografias, requisitos
        self.validar()

    def eliminar(self) -> None:
        """Borrado lógico. En el Día 2 se agrega la regla: no se elimina con solicitudes pendientes o reserva activa."""
        self.estado = EstadoInmueble.ELIMINADO
        self.disponibilidad = False
