"""Adaptadores de salida: solicitudes, reservas y pagos con PostgreSQL."""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dominio.solicitud import (
    EstadoPago, EstadoReserva, EstadoSolicitud, Pago, Reserva, Solicitud,
)
from app.puertos.repositorios import RepositorioPagos, RepositorioReservas, RepositorioSolicitudes

from .modelos_orm import PagoORM, ReservaORM, SolicitudORM


def _sol_a_dominio(f: SolicitudORM) -> Solicitud:
    return Solicitud(
        id_solicitud=f.id_solicitud, estudiante_id=f.estudiante_id, inmueble_id=f.inmueble_id,
        estado=EstadoSolicitud(f.estado), fecha_solicitud=f.fecha_solicitud,
    )


def _res_a_dominio(f: ReservaORM) -> Reserva:
    return Reserva(
        id_reserva=f.id_reserva, solicitud_id=f.solicitud_id, inmueble_id=f.inmueble_id,
        estudiante_id=f.estudiante_id, arrendador_id=f.arrendador_id, fecha_inicio=f.fecha_inicio,
        monto=f.monto, estado=EstadoReserva(f.estado), fecha_creacion=f.fecha_creacion,
    )


def _pag_a_dominio(f: PagoORM) -> Pago:
    return Pago(
        id_pago=f.id_pago, reserva_id=f.reserva_id, monto=f.monto, pasarela=f.pasarela,
        referencia=f.referencia, estado=EstadoPago(f.estado), fecha_pago=f.fecha_pago,
    )


class RepositorioSolicitudesSQL(RepositorioSolicitudes):
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def guardar(self, s: Solicitud) -> Solicitud:
        fila = self.sesion.get(SolicitudORM, s.id_solicitud) if s.id_solicitud else SolicitudORM()
        fila.estudiante_id, fila.inmueble_id = s.estudiante_id, s.inmueble_id
        fila.estado, fila.fecha_solicitud = s.estado.value, s.fecha_solicitud
        self.sesion.add(fila)
        self.sesion.commit()
        return _sol_a_dominio(fila)

    def buscar_por_id(self, id_solicitud: int) -> Optional[Solicitud]:
        fila = self.sesion.get(SolicitudORM, id_solicitud)
        return _sol_a_dominio(fila) if fila else None

    def listar_del_estudiante(self, estudiante_id: int) -> List[Solicitud]:
        q = select(SolicitudORM).where(SolicitudORM.estudiante_id == estudiante_id).order_by(SolicitudORM.fecha_solicitud.desc())
        return [_sol_a_dominio(f) for f in self.sesion.scalars(q).all()]

    def listar_del_arrendador(self, arrendador_id: int) -> List[Solicitud]:
        from .modelos_orm import InmuebleORM
        q = (select(SolicitudORM).join(InmuebleORM, SolicitudORM.inmueble_id == InmuebleORM.id_inmueble)
             .where(InmuebleORM.arrendador_id == arrendador_id)
             .order_by(SolicitudORM.fecha_solicitud.desc()))
        return [_sol_a_dominio(f) for f in self.sesion.scalars(q).all()]

    def hay_solicitud_activa(self, estudiante_id: int, inmueble_id: int) -> bool:
        activos = (EstadoSolicitud.PENDIENTE.value, EstadoSolicitud.APROBADA.value)
        q = select(SolicitudORM).where(
            SolicitudORM.estudiante_id == estudiante_id,
            SolicitudORM.inmueble_id == inmueble_id,
            SolicitudORM.estado.in_(activos),
        )
        return self.sesion.scalar(q) is not None


class RepositorioReservasSQL(RepositorioReservas):
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def guardar(self, r: Reserva) -> Reserva:
        fila = self.sesion.get(ReservaORM, r.id_reserva) if r.id_reserva else ReservaORM()
        fila.solicitud_id, fila.inmueble_id = r.solicitud_id, r.inmueble_id
        fila.estudiante_id, fila.arrendador_id = r.estudiante_id, r.arrendador_id
        fila.fecha_inicio, fila.monto = r.fecha_inicio, r.monto
        fila.estado, fila.fecha_creacion = r.estado.value, r.fecha_creacion
        self.sesion.add(fila)
        self.sesion.commit()
        return _res_a_dominio(fila)

    def buscar_por_id(self, id_reserva: int) -> Optional[Reserva]:
        fila = self.sesion.get(ReservaORM, id_reserva)
        return _res_a_dominio(fila) if fila else None

    def buscar_por_solicitud(self, id_solicitud: int) -> Optional[Reserva]:
        fila = self.sesion.scalar(select(ReservaORM).where(ReservaORM.solicitud_id == id_solicitud))
        return _res_a_dominio(fila) if fila else None


class RepositorioPagosSQL(RepositorioPagos):
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def guardar(self, p: Pago) -> Pago:
        fila = self.sesion.get(PagoORM, p.id_pago) if p.id_pago else PagoORM()
        fila.reserva_id, fila.monto, fila.pasarela = p.reserva_id, p.monto, p.pasarela
        fila.referencia, fila.estado, fila.fecha_pago = p.referencia, p.estado.value, p.fecha_pago
        self.sesion.add(fila)
        self.sesion.commit()
        return _pag_a_dominio(fila)

    def buscar_por_reserva(self, id_reserva: int) -> Optional[Pago]:
        fila = self.sesion.scalar(select(PagoORM).where(PagoORM.reserva_id == id_reserva))
        return _pag_a_dominio(fila) if fila else None

    def buscar_por_referencia(self, referencia: str) -> Optional[Pago]:
        fila = self.sesion.scalar(select(PagoORM).where(PagoORM.referencia == referencia))
        return _pag_a_dominio(fila) if fila else None
