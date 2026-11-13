"""Casos de uso de Pago. El Pago lo INICIA el Arrendador (A15); el estudiante solo consulta (E12)."""
from app.dominio.errores import ErrorDominio, NoAutorizado, NoEncontrado
from app.dominio.solicitud import EstadoPago, EstadoReserva
from app.dominio.usuario import Usuario
from app.puertos.pasarela import PasarelaPagos
from app.puertos.repositorios import (
    RepositorioInmuebles, RepositorioPagos, RepositorioReservas,
)


class IniciarPago:
    """A15: el arrendador genera la sesión de Stripe. Devuelve la URL donde el estudiante paga."""

    def __init__(
        self,
        repo_r: RepositorioReservas,
        repo_p: RepositorioPagos,
        repo_i: RepositorioInmuebles,
        pasarela: PasarelaPagos,
    ):
        self.repo_r, self.repo_p, self.repo_i, self.pasarela = repo_r, repo_p, repo_i, pasarela

    def ejecutar(self, arrendador: Usuario, id_reserva: int) -> dict:
        reserva = self.repo_r.buscar_por_id(id_reserva)
        if not reserva:
            raise NoEncontrado("La reserva no existe")
        if reserva.arrendador_id != arrendador.id_usuario:
            raise NoAutorizado("Solo el arrendador dueño inicia el pago")
        if reserva.estado != EstadoReserva.ACTIVA:
            raise ErrorDominio("La reserva no está activa")
        pago = self.repo_p.buscar_por_reserva(id_reserva)
        if not pago:
            raise NoEncontrado("No hay pago asociado a esta reserva")
        if pago.estado == EstadoPago.APROBADO:
            raise ErrorDominio("El pago ya fue aprobado")
        inmueble = self.repo_i.buscar_por_id(reserva.inmueble_id)
        sesion = self.pasarela.crear_sesion(
            monto=pago.monto,
            moneda="cop",
            descripcion=f"Reserva de {inmueble.titulo if inmueble else 'inmueble'}",
            metadata={"id_reserva": reserva.id_reserva, "id_pago": pago.id_pago},
        )
        pago.iniciar(sesion.referencia)
        self.repo_p.guardar(pago)
        return {"url_pago": sesion.url_pago, "referencia": sesion.referencia}


class ConsultarEstadoPago:
    """E12: el estudiante consulta el estado de su pago."""

    def __init__(self, repo_p: RepositorioPagos, repo_r: RepositorioReservas):
        self.repo_p, self.repo_r = repo_p, repo_r

    def ejecutar(self, usuario: Usuario, id_pago: int):
        pagos = [p for p in [self.repo_p.buscar_por_reserva(r) for r in [id_pago]] if p]
        pago = pagos[0] if pagos else None
        if not pago:
            raise NoEncontrado("Pago no encontrado")
        reserva = self.repo_r.buscar_por_id(pago.reserva_id)
        if reserva and usuario.id_usuario not in (reserva.estudiante_id, reserva.arrendador_id):
            raise NoAutorizado("No tienes acceso a este pago")
        return pago


class ProcesarEventoPago:
    """Caso de uso que recibe el webhook de Stripe y actualiza el estado del Pago.

    Si el pago es aprobado:
      - Pago -> aprobado
      - Reserva -> confirmada
      - Inmueble -> disponibilidad=False (ya está arrendado)
    """

    def __init__(
        self,
        repo_p: RepositorioPagos,
        repo_r: RepositorioReservas,
        repo_i: RepositorioInmuebles,
        pasarela: PasarelaPagos,
    ):
        self.repo_p, self.repo_r, self.repo_i, self.pasarela = repo_p, repo_r, repo_i, pasarela

    def ejecutar(self, cuerpo: bytes, firma: str) -> None:
        resultado = self.pasarela.leer_evento(cuerpo, firma)
        if resultado is None:
            return  # evento que no nos interesa
        pago = self.repo_p.buscar_por_referencia(resultado.referencia)
        if not pago:
            return
        if resultado.aprobado:
            pago.actualizar_estado(EstadoPago.APROBADO)
            self.repo_p.guardar(pago)
            reserva = self.repo_r.buscar_por_id(pago.reserva_id)
            if reserva:
                reserva.confirmar()
                self.repo_r.guardar(reserva)
                inmueble = self.repo_i.buscar_por_id(reserva.inmueble_id)
                if inmueble:
                    inmueble.actualizar_disponibilidad(False)
                    self.repo_i.guardar(inmueble)
        else:
            pago.actualizar_estado(EstadoPago.RECHAZADO)
            self.repo_p.guardar(pago)
