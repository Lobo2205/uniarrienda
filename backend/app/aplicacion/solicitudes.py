"""Casos de uso de Solicitud y Reserva."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple

from app.dominio.errores import Conflicto, ErrorDominio, NoAutorizado, NoEncontrado
from app.dominio.inmueble import Inmueble
from app.dominio.solicitud import EstadoSolicitud, Pago, Reserva, Solicitud
from app.dominio.usuario import Usuario
from app.puertos.repositorios import (
    RepositorioInmuebles, RepositorioPagos, RepositorioReservas, RepositorioSolicitudes,
)


class CrearSolicitud:
    """Pantalla E09: el estudiante solicita un inmueble."""

    def __init__(self, repo_solicitudes: RepositorioSolicitudes, repo_inmuebles: RepositorioInmuebles):
        self.repo = repo_solicitudes
        self.repo_inmuebles = repo_inmuebles

    def ejecutar(self, estudiante: Usuario, inmueble_id: int) -> Solicitud:
        if not estudiante.es_estudiante:
            raise NoAutorizado("Solo un estudiante puede solicitar un inmueble")
        inmueble = self.repo_inmuebles.buscar_por_id(inmueble_id)
        if not inmueble:
            raise NoEncontrado("El inmueble no existe")
        if not inmueble.disponibilidad:
            raise ErrorDominio("El inmueble ya no está disponible")
        if inmueble.arrendador_id == estudiante.id_usuario:
            raise ErrorDominio("No puedes solicitar tu propio inmueble")
        if self.repo.hay_solicitud_activa(estudiante.id_usuario, inmueble_id):
            raise Conflicto("Ya enviaste una solicitud para este inmueble")
        solicitud = Solicitud(estudiante_id=estudiante.id_usuario, inmueble_id=inmueble_id)
        return self.repo.guardar(solicitud)


class ListarMisSolicitudes:
    """E10: solicitudes del estudiante que inició sesión."""

    def __init__(self, repo: RepositorioSolicitudes):
        self.repo = repo

    def ejecutar(self, estudiante: Usuario) -> List[Solicitud]:
        if not estudiante.es_estudiante:
            raise NoAutorizado("Solo el estudiante ve sus solicitudes")
        return self.repo.listar_del_estudiante(estudiante.id_usuario)


class ListarSolicitudesDelArrendador:
    """A13: solicitudes recibidas por el arrendador."""

    def __init__(self, repo: RepositorioSolicitudes):
        self.repo = repo

    def ejecutar(self, arrendador: Usuario) -> List[Solicitud]:
        if not arrendador.es_arrendador:
            raise NoAutorizado("Solo el arrendador ve sus solicitudes recibidas")
        return self.repo.listar_del_arrendador(arrendador.id_usuario)


class CancelarSolicitud:
    """E11: el estudiante cancela una solicitud pendiente."""

    def __init__(self, repo: RepositorioSolicitudes):
        self.repo = repo

    def ejecutar(self, usuario: Usuario, id_solicitud: int) -> Solicitud:
        solicitud = self.repo.buscar_por_id(id_solicitud)
        if not solicitud:
            raise NoEncontrado("La solicitud no existe")
        solicitud.cancelar(usuario.id_usuario)
        return self.repo.guardar(solicitud)


def _solicitud_e_inmueble(
    repo_s: RepositorioSolicitudes, repo_i: RepositorioInmuebles, id_solicitud: int
) -> Tuple[Solicitud, Inmueble]:
    solicitud = repo_s.buscar_por_id(id_solicitud)
    if not solicitud:
        raise NoEncontrado("La solicitud no existe")
    inmueble = repo_i.buscar_por_id(solicitud.inmueble_id)
    if not inmueble:
        raise NoEncontrado("El inmueble asociado no existe")
    return solicitud, inmueble


@dataclass
class DatosAprobacion:
    fecha_inicio: datetime


class AprobarSolicitud:
    """A14: el arrendador aprueba y se crea automáticamente la Reserva."""

    def __init__(
        self,
        repo_s: RepositorioSolicitudes,
        repo_i: RepositorioInmuebles,
        repo_r: RepositorioReservas,
        repo_p: RepositorioPagos,
    ):
        self.repo_s, self.repo_i, self.repo_r, self.repo_p = repo_s, repo_i, repo_r, repo_p

    def ejecutar(self, arrendador: Usuario, id_solicitud: int, datos: DatosAprobacion) -> Reserva:
        solicitud, inmueble = _solicitud_e_inmueble(self.repo_s, self.repo_i, id_solicitud)
        if not inmueble.disponibilidad:
            raise ErrorDominio("El inmueble ya no está disponible")
        solicitud.actualizar_estado(EstadoSolicitud.APROBADA, arrendador.id_usuario, inmueble.arrendador_id)
        self.repo_s.guardar(solicitud)
        reserva = Reserva(
            solicitud_id=solicitud.id_solicitud,
            inmueble_id=inmueble.id_inmueble,
            estudiante_id=solicitud.estudiante_id,
            arrendador_id=inmueble.arrendador_id,
            fecha_inicio=datos.fecha_inicio,
            monto=inmueble.precio,
        )
        reserva = self.repo_r.guardar(reserva)
        self.repo_p.guardar(Pago(reserva_id=reserva.id_reserva, monto=reserva.monto))
        return reserva


class RechazarSolicitud:
    """A14: el arrendador rechaza. Las demás solicitudes del inmueble siguen activas."""

    def __init__(self, repo_s: RepositorioSolicitudes, repo_i: RepositorioInmuebles):
        self.repo_s, self.repo_i = repo_s, repo_i

    def ejecutar(self, arrendador: Usuario, id_solicitud: int) -> Solicitud:
        solicitud, inmueble = _solicitud_e_inmueble(self.repo_s, self.repo_i, id_solicitud)
        solicitud.actualizar_estado(EstadoSolicitud.RECHAZADA, arrendador.id_usuario, inmueble.arrendador_id)
        return self.repo_s.guardar(solicitud)


class ConsultarReserva:
    """E12 y A15: traer la reserva y el pago asociado."""

    def __init__(self, repo_r: RepositorioReservas, repo_p: RepositorioPagos):
        self.repo_r, self.repo_p = repo_r, repo_p

    def ejecutar(self, usuario: Usuario, id_reserva: int) -> Tuple[Reserva, Pago]:
        reserva = self.repo_r.buscar_por_id(id_reserva)
        if not reserva:
            raise NoEncontrado("La reserva no existe")
        if usuario.id_usuario not in (reserva.estudiante_id, reserva.arrendador_id):
            raise NoAutorizado("No tienes acceso a esta reserva")
        pago = self.repo_p.buscar_por_reserva(reserva.id_reserva)
        if not pago:
            raise NoEncontrado("El pago aún no existe")
        return reserva, pago


class CancelarReserva:
    """E12 / A15: se puede cancelar mientras el pago no esté aprobado."""

    def __init__(self, repo_r: RepositorioReservas, repo_i: RepositorioInmuebles):
        self.repo_r, self.repo_i = repo_r, repo_i

    def ejecutar(self, usuario: Usuario, id_reserva: int) -> Reserva:
        reserva = self.repo_r.buscar_por_id(id_reserva)
        if not reserva:
            raise NoEncontrado("La reserva no existe")
        reserva.cancelar(usuario.id_usuario)
        # Si estaba marcado no disponible por una reserva activa, se podría reactivar aquí. Simple: dejamos que el arrendador lo haga desde A11.
        return self.repo_r.guardar(reserva)
