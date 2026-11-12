"""Adaptador de salida: implementa RepositorioInmuebles con PostgreSQL."""
from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.dominio.inmueble import (
    Especificaciones, EstadoInmueble, Fotografia, Inmueble, Requisito, TipoInmueble, Ubicacion,
)
from app.puertos.repositorios import FiltrosInmueble, RepositorioInmuebles

from .modelos_orm import FotografiaORM, InmuebleORM, RequisitoORM, UbicacionORM

ESPECS = ["habitaciones", "banos", "cocina", "estacionamiento", "mascotas", "wifi", "servicios_incluidos"]


def _a_dominio(f: InmuebleORM) -> Inmueble:
    u = f.ubicacion
    return Inmueble(
        id_inmueble=f.id_inmueble, arrendador_id=f.arrendador_id, titulo=f.titulo, descripcion=f.descripcion,
        precio=f.precio, tipo=TipoInmueble(f.tipo), disponibilidad=f.disponibilidad,
        estado=EstadoInmueble(f.estado), fecha_publicacion=f.fecha_publicacion,
        ubicacion=Ubicacion(u.direccion, u.barrio, u.latitud, u.longitud),
        especificaciones=Especificaciones(**{k: getattr(f, k) for k in ESPECS}),
        fotografias=[Fotografia(x.url, x.espacio) for x in f.fotografias],
        requisitos=[Requisito(x.descripcion) for x in f.requisitos],
    )


class RepositorioInmueblesSQL(RepositorioInmuebles):
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def guardar(self, i: Inmueble) -> Inmueble:
        fila = self.sesion.get(InmuebleORM, i.id_inmueble) if i.id_inmueble else InmuebleORM()
        fila.arrendador_id, fila.titulo, fila.descripcion = i.arrendador_id, i.titulo, i.descripcion
        fila.precio, fila.tipo, fila.disponibilidad = i.precio, i.tipo.value, i.disponibilidad
        fila.estado, fila.fecha_publicacion = i.estado.value, i.fecha_publicacion
        for k in ESPECS:
            setattr(fila, k, getattr(i.especificaciones, k))
        u = i.ubicacion
        if fila.ubicacion is None:
            fila.ubicacion = UbicacionORM()
        fila.ubicacion.direccion, fila.ubicacion.barrio = u.direccion, u.barrio
        fila.ubicacion.latitud, fila.ubicacion.longitud = u.latitud, u.longitud
        fila.fotografias = [FotografiaORM(url=x.url, espacio=x.espacio) for x in i.fotografias]
        fila.requisitos = [RequisitoORM(descripcion=x.descripcion) for x in i.requisitos]
        self.sesion.add(fila)
        self.sesion.commit()
        return _a_dominio(fila)

    def buscar_por_id(self, id_inmueble: int) -> Optional[Inmueble]:
        fila = self.sesion.get(InmuebleORM, id_inmueble)
        return _a_dominio(fila) if fila else None

    def buscar(self, f: FiltrosInmueble) -> List[Inmueble]:
        q = select(InmuebleORM).join(InmuebleORM.ubicacion).where(InmuebleORM.estado == EstadoInmueble.PUBLICADO.value)
        if f.solo_disponibles:
            q = q.where(InmuebleORM.disponibilidad.is_(True))
        if f.tipo:
            q = q.where(InmuebleORM.tipo == f.tipo.value)
        if f.precio_min is not None:
            q = q.where(InmuebleORM.precio >= f.precio_min)
        if f.precio_max is not None:
            q = q.where(InmuebleORM.precio <= f.precio_max)
        if f.barrio:
            q = q.where(UbicacionORM.barrio.ilike(f"%{f.barrio}%"))
        if f.texto:
            t = f"%{f.texto}%"
            q = q.where(or_(InmuebleORM.titulo.ilike(t), InmuebleORM.descripcion.ilike(t), UbicacionORM.barrio.ilike(t)))
        if f.wifi:
            q = q.where(InmuebleORM.wifi.is_(True))
        if f.mascotas:
            q = q.where(InmuebleORM.mascotas.is_(True))
        q = q.order_by(InmuebleORM.fecha_publicacion.desc())
        return [_a_dominio(x) for x in self.sesion.scalars(q).unique().all()]

    def listar_de_arrendador(self, arrendador_id: int) -> List[Inmueble]:
        q = (select(InmuebleORM).where(InmuebleORM.arrendador_id == arrendador_id,
                                       InmuebleORM.estado != EstadoInmueble.ELIMINADO.value)
             .order_by(InmuebleORM.fecha_publicacion.desc()))
        return [_a_dominio(x) for x in self.sesion.scalars(q).unique().all()]
