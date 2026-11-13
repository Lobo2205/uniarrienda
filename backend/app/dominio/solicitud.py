"""Solicitud, Reserva y Pago del modelo V7.

Relación clave del negocio: una Solicitud aprobada genera una Reserva,
y de la Reserva sale el Pago (un Pago por Reserva). El Pago lo inicia el
Arrendador y el Estudiante solo consulta su estado.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from .errores import ErrorDominio, NoAutorizado


class EstadoSolicitud(str, Enum):
    PENDIENTE = "pendiente"
    APROBADA = "aprobada"
    RECHAZADA = "rechazada"
    CANCELADA = "cancelada"


class EstadoReserva(str, Enum):
    ACTIVA = "activa"
    CANCELADA = "cancelada"
    CONFIRMADA = "confirmada"  # cuando el pago se aprueba


class EstadoPago(str, Enum):
    SIN_INICIAR = "sin_iniciar"
    PENDIENTE = "pendiente"       # el estudiante aún no completa en Stripe
    CONFIRMANDO = "confirmando"   # Stripe no respondió a tiempo
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"


@dataclass
class Solicitud:
    estudiante_id: int
    inmueble_id: int
    estado: EstadoSolicitud = EstadoSolicitud.PENDIENTE
    fecha_solicitud: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id_solicitud: Optional[int] = None

    # ---- Reglas del negocio ----
    def actualizar_estado(self, nuevo: EstadoSolicitud, por_usuario_id: int, dueno_id: int) -> None:
        """Aprobar o rechazar solo lo hace el arrendador dueño del inmueble."""
        if nuevo in (EstadoSolicitud.APROBADA, EstadoSolicitud.RECHAZADA):
            if por_usuario_id != dueno_id:
                raise NoAutorizado("Solo el arrendador dueño puede aprobar o rechazar")
        if self.estado != EstadoSolicitud.PENDIENTE:
            raise ErrorDominio("Esta solicitud ya no está pendiente")
        self.estado = nuevo

    def cancelar(self, por_usuario_id: int) -> None:
        """El estudiante que la envió puede cancelarla si sigue pendiente."""
        if por_usuario_id != self.estudiante_id:
            raise NoAutorizado("Solo el estudiante que la envió puede cancelarla")
        if self.estado != EstadoSolicitud.PENDIENTE:
            raise ErrorDominio("La solicitud ya no está pendiente")
        self.estado = EstadoSolicitud.CANCELADA


@dataclass
class Reserva:
    solicitud_id: int
    inmueble_id: int
    estudiante_id: int
    arrendador_id: int
    fecha_inicio: datetime  # la define el arrendador al aprobar
    monto: int              # pesos colombianos
    estado: EstadoReserva = EstadoReserva.ACTIVA
    fecha_creacion: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id_reserva: Optional[int] = None

    def cancelar(self, por_usuario_id: int) -> None:
        if por_usuario_id not in (self.arrendador_id, self.estudiante_id):
            raise NoAutorizado("No puedes cancelar esta reserva")
        if self.estado == EstadoReserva.CONFIRMADA:
            raise ErrorDominio("La reserva ya tiene un pago confirmado; no puede cancelarse")
        self.estado = EstadoReserva.CANCELADA

    def confirmar(self) -> None:
        self.estado = EstadoReserva.CONFIRMADA


@dataclass
class Pago:
    reserva_id: int
    monto: int
    pasarela: str = "stripe"
    referencia: Optional[str] = None  # id de la sesión de Stripe
    estado: EstadoPago = EstadoPago.SIN_INICIAR
    fecha_pago: Optional[datetime] = None
    id_pago: Optional[int] = None

    def iniciar(self, referencia: str) -> None:
        if self.estado not in (EstadoPago.SIN_INICIAR, EstadoPago.RECHAZADO):
            raise ErrorDominio("El pago ya está en curso")
        self.referencia = referencia
        self.estado = EstadoPago.PENDIENTE

    def actualizar_estado(self, nuevo: EstadoPago) -> None:
        self.estado = nuevo
        if nuevo == EstadoPago.APROBADO:
            self.fecha_pago = datetime.now(timezone.utc)
