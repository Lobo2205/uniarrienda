"""Puertos de salida: lo que el negocio necesita guardar y consultar.

Son contratos (clases abstractas). Los adaptadores de salida los implementan con PostgreSQL.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from app.dominio.inmueble import Inmueble, TipoInmueble
from app.dominio.solicitud import Pago, Reserva, Solicitud
from app.dominio.usuario import Usuario


class RepositorioUsuarios(ABC):
    @abstractmethod
    def guardar(self, usuario: Usuario) -> Usuario: ...

    @abstractmethod
    def buscar_por_correo(self, correo: str) -> Optional[Usuario]: ...

    @abstractmethod
    def buscar_por_id(self, id_usuario: int) -> Optional[Usuario]: ...


@dataclass
class FiltrosInmueble:
    texto: Optional[str] = None
    tipo: Optional[TipoInmueble] = None
    precio_min: Optional[int] = None
    precio_max: Optional[int] = None
    barrio: Optional[str] = None
    wifi: Optional[bool] = None
    mascotas: Optional[bool] = None
    solo_disponibles: bool = True


class RepositorioInmuebles(ABC):
    @abstractmethod
    def guardar(self, inmueble: Inmueble) -> Inmueble: ...

    @abstractmethod
    def buscar_por_id(self, id_inmueble: int) -> Optional[Inmueble]: ...

    @abstractmethod
    def buscar(self, filtros: FiltrosInmueble) -> List[Inmueble]: ...

    @abstractmethod
    def listar_de_arrendador(self, arrendador_id: int) -> List[Inmueble]: ...


class RepositorioSolicitudes(ABC):
    @abstractmethod
    def guardar(self, solicitud: Solicitud) -> Solicitud: ...

    @abstractmethod
    def buscar_por_id(self, id_solicitud: int) -> Optional[Solicitud]: ...

    @abstractmethod
    def listar_del_estudiante(self, estudiante_id: int) -> List[Solicitud]: ...

    @abstractmethod
    def listar_del_arrendador(self, arrendador_id: int) -> List[Solicitud]: ...

    @abstractmethod
    def hay_solicitud_activa(self, estudiante_id: int, inmueble_id: int) -> bool:
        """True si el estudiante ya tiene una solicitud pendiente o aprobada para ese inmueble."""


class RepositorioReservas(ABC):
    @abstractmethod
    def guardar(self, reserva: Reserva) -> Reserva: ...

    @abstractmethod
    def buscar_por_id(self, id_reserva: int) -> Optional[Reserva]: ...

    @abstractmethod
    def buscar_por_solicitud(self, id_solicitud: int) -> Optional[Reserva]: ...


class RepositorioPagos(ABC):
    @abstractmethod
    def guardar(self, pago: Pago) -> Pago: ...

    @abstractmethod
    def buscar_por_reserva(self, id_reserva: int) -> Optional[Pago]: ...

    @abstractmethod
    def buscar_por_referencia(self, referencia: str) -> Optional[Pago]: ...
