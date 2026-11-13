"""Adaptador de entrada: endpoints de solicitudes, reservas y pagos."""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from app.aplicacion.pagos import IniciarPago, ProcesarEventoPago
from app.aplicacion.solicitudes import (
    AprobarSolicitud, CancelarReserva, CancelarSolicitud, ConsultarReserva, CrearSolicitud,
    DatosAprobacion, ListarMisSolicitudes, ListarSolicitudesDelArrendador, RechazarSolicitud,
)
from app.dominio.errores import NoEncontrado
from app.dominio.usuario import Usuario
from app.infraestructura.dependencias import (
    pasarela, repo_inmuebles, repo_pagos, repo_reservas, repo_solicitudes, repo_usuarios, usuario_actual,
)

router = APIRouter(tags=["Solicitudes y pagos"])


# ---------- Esquemas ----------
class SolicitudCrear(BaseModel):
    inmueble_id: int


class SolicitudSalida(BaseModel):
    id_solicitud: int
    estudiante_id: int
    inmueble_id: int
    estado: str
    fecha_solicitud: datetime
    # Datos extra para que Flutter y React no tengan que hacer varias peticiones
    inmueble_titulo: str | None = None
    inmueble_precio: int | None = None
    inmueble_foto: str | None = None
    estudiante_nombre: str | None = None
    estudiante_universidad: str | None = None
    id_reserva: int | None = None


class AprobacionEntrada(BaseModel):
    fecha_inicio: datetime


class ReservaSalida(BaseModel):
    id_reserva: int
    solicitud_id: int
    inmueble_id: int
    estudiante_id: int
    arrendador_id: int
    fecha_inicio: datetime
    monto: int
    estado: str
    fecha_creacion: datetime


class PagoSalida(BaseModel):
    id_pago: int
    reserva_id: int
    monto: int
    pasarela: str
    referencia: str | None
    estado: str
    fecha_pago: datetime | None


class ReservaConPago(BaseModel):
    reserva: ReservaSalida
    pago: PagoSalida
    url_pago: str | None = None  # solo si el pago está pendiente: el estudiante paga aquí


class InicioPagoSalida(BaseModel):
    url_pago: str
    referencia: str


# ---------- Solicitudes ----------

def _sol(s, ri=None, ru=None, rr=None):
    salida = SolicitudSalida(id_solicitud=s.id_solicitud, estudiante_id=s.estudiante_id,
                             inmueble_id=s.inmueble_id, estado=s.estado.value, fecha_solicitud=s.fecha_solicitud)
    if ri:
        i = ri.buscar_por_id(s.inmueble_id)
        if i:
            salida.inmueble_titulo, salida.inmueble_precio = i.titulo, i.precio
            salida.inmueble_foto = i.fotografias[0].url if i.fotografias else None
    if ru:
        u = ru.buscar_por_id(s.estudiante_id)
        if u:
            salida.estudiante_nombre, salida.estudiante_universidad = u.nombre, u.universidad
    if rr:
        r = rr.buscar_por_solicitud(s.id_solicitud)
        salida.id_reserva = r.id_reserva if r else None
    return salida


def _res(r):
    return ReservaSalida(id_reserva=r.id_reserva, solicitud_id=r.solicitud_id, inmueble_id=r.inmueble_id,
                         estudiante_id=r.estudiante_id, arrendador_id=r.arrendador_id,
                         fecha_inicio=r.fecha_inicio, monto=r.monto, estado=r.estado.value,
                         fecha_creacion=r.fecha_creacion)


def _pag(p):
    return PagoSalida(id_pago=p.id_pago, reserva_id=p.reserva_id, monto=p.monto, pasarela=p.pasarela,
                      referencia=p.referencia, estado=p.estado.value, fecha_pago=p.fecha_pago)


@router.post("/solicitudes", response_model=SolicitudSalida, status_code=status.HTTP_201_CREATED)
def crear_solicitud(datos: SolicitudCrear, yo: Usuario = Depends(usuario_actual),
                    rs=Depends(repo_solicitudes), ri=Depends(repo_inmuebles)):
    s = CrearSolicitud(rs, ri).ejecutar(yo, datos.inmueble_id)
    return _sol(s)


@router.get("/solicitudes/mias", response_model=List[SolicitudSalida])
def mis_solicitudes(yo: Usuario = Depends(usuario_actual), rs=Depends(repo_solicitudes),
                    ri=Depends(repo_inmuebles), ru=Depends(repo_usuarios), rr=Depends(repo_reservas)):
    return [_sol(s, ri, ru, rr) for s in ListarMisSolicitudes(rs).ejecutar(yo)]


@router.get("/solicitudes/recibidas", response_model=List[SolicitudSalida])
def solicitudes_recibidas(yo: Usuario = Depends(usuario_actual), rs=Depends(repo_solicitudes),
                          ri=Depends(repo_inmuebles), ru=Depends(repo_usuarios), rr=Depends(repo_reservas)):
    return [_sol(s, ri, ru, rr) for s in ListarSolicitudesDelArrendador(rs).ejecutar(yo)]


@router.post("/solicitudes/{id_solicitud}/cancelar", response_model=SolicitudSalida)
def cancelar(id_solicitud: int, yo: Usuario = Depends(usuario_actual), rs=Depends(repo_solicitudes)):
    s = CancelarSolicitud(rs).ejecutar(yo, id_solicitud)
    return _sol(s)


@router.post("/solicitudes/{id_solicitud}/aprobar", response_model=ReservaSalida, status_code=status.HTTP_201_CREATED)
def aprobar(id_solicitud: int, datos: AprobacionEntrada, yo: Usuario = Depends(usuario_actual),
            rs=Depends(repo_solicitudes), ri=Depends(repo_inmuebles), rr=Depends(repo_reservas), rp=Depends(repo_pagos)):
    r = AprobarSolicitud(rs, ri, rr, rp).ejecutar(yo, id_solicitud, DatosAprobacion(fecha_inicio=datos.fecha_inicio))
    return _res(r)


@router.post("/solicitudes/{id_solicitud}/rechazar", response_model=SolicitudSalida)
def rechazar(id_solicitud: int, yo: Usuario = Depends(usuario_actual),
             rs=Depends(repo_solicitudes), ri=Depends(repo_inmuebles)):
    s = RechazarSolicitud(rs, ri).ejecutar(yo, id_solicitud)
    return _sol(s)


# ---------- Reservas y pagos ----------
def _reserva_con_pago(r, p, pg=None) -> ReservaConPago:
    url = pg.obtener_url(p.referencia) if (pg and p.referencia and p.estado.value == "pendiente") else None
    return ReservaConPago(reserva=_res(r), pago=_pag(p), url_pago=url)


@router.get("/reservas/por-solicitud/{id_solicitud}", response_model=ReservaConPago)
def ver_reserva_por_solicitud(id_solicitud: int, yo: Usuario = Depends(usuario_actual),
                              rr=Depends(repo_reservas), rp=Depends(repo_pagos), pg=Depends(pasarela)):
    """Desde una solicitud aprobada, llegar a su reserva (E11 → E12, A14 → A15)."""
    reserva = rr.buscar_por_solicitud(id_solicitud)
    if not reserva:
        raise NoEncontrado("Esta solicitud aún no tiene reserva")
    r, p = ConsultarReserva(rr, rp).ejecutar(yo, reserva.id_reserva)
    return _reserva_con_pago(r, p, pg)


@router.get("/reservas/{id_reserva}", response_model=ReservaConPago)
def ver_reserva(id_reserva: int, yo: Usuario = Depends(usuario_actual),
                rr=Depends(repo_reservas), rp=Depends(repo_pagos), pg=Depends(pasarela)):
    r, p = ConsultarReserva(rr, rp).ejecutar(yo, id_reserva)
    return _reserva_con_pago(r, p, pg)


@router.post("/reservas/{id_reserva}/cancelar", response_model=ReservaSalida)
def cancelar_reserva(id_reserva: int, yo: Usuario = Depends(usuario_actual),
                     rr=Depends(repo_reservas), ri=Depends(repo_inmuebles)):
    r = CancelarReserva(rr, ri).ejecutar(yo, id_reserva)
    return _res(r)


@router.post("/reservas/{id_reserva}/iniciar-pago", response_model=InicioPagoSalida)
def iniciar_pago(id_reserva: int, yo: Usuario = Depends(usuario_actual),
                 rr=Depends(repo_reservas), rp=Depends(repo_pagos), ri=Depends(repo_inmuebles), pg=Depends(pasarela)):
    datos = IniciarPago(rr, rp, ri, pg).ejecutar(yo, id_reserva)
    return InicioPagoSalida(**datos)


# ---------- Webhook de la pasarela ----------
@router.post("/pagos/webhook", status_code=status.HTTP_200_OK)
async def webhook_pago(request: Request, rp=Depends(repo_pagos), rr=Depends(repo_reservas),
                       ri=Depends(repo_inmuebles), pg=Depends(pasarela)):
    cuerpo = await request.body()
    firma = request.headers.get("stripe-signature", "")
    ProcesarEventoPago(rp, rr, ri, pg).ejecutar(cuerpo, firma)
    return {"recibido": True}


@router.get("/pagos/falso/confirmar", include_in_schema=False)
def _falso_pagar(referencia: str, aprobado: bool = True,
                 rp=Depends(repo_pagos), rr=Depends(repo_reservas), ri=Depends(repo_inmuebles), pg=Depends(pasarela)):
    """Solo con la pasarela falsa: simula que el estudiante pagó entrando a la URL."""
    import json
    cuerpo = json.dumps({"referencia": referencia, "aprobado": aprobado}).encode()
    ProcesarEventoPago(rp, rr, ri, pg).ejecutar(cuerpo, "")
    return {"ok": True, "aprobado": aprobado}
