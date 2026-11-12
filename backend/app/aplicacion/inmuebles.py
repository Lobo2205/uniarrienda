"""Casos de uso de Inmueble: publicar, buscar, ver detalle, listar los propios y cambiar disponibilidad."""
from dataclasses import dataclass, field
from typing import List, Optional

from app.dominio.errores import ErrorDominio, NoAutorizado, NoEncontrado
from app.dominio.inmueble import (
    Especificaciones, EstadoInmueble, Fotografia, Inmueble, Requisito, TipoInmueble, Ubicacion,
)
from app.dominio.usuario import Usuario
from app.puertos.repositorios import FiltrosInmueble, RepositorioInmuebles


@dataclass
class DatosInmueble:
    titulo: str
    descripcion: str
    precio: int
    tipo: TipoInmueble
    direccion: str
    barrio: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    especificaciones: Especificaciones = field(default_factory=Especificaciones)
    fotografias: List[Fotografia] = field(default_factory=list)
    requisitos: List[str] = field(default_factory=list)


class PublicarInmueble:
    def __init__(self, repo: RepositorioInmuebles):
        self.repo = repo

    def ejecutar(self, arrendador: Usuario, datos: DatosInmueble) -> Inmueble:
        if not arrendador.es_arrendador:
            raise NoAutorizado("Solo un arrendador puede publicar inmuebles")
        inmueble = Inmueble(
            arrendador_id=arrendador.id_usuario,
            titulo=datos.titulo,
            descripcion=datos.descripcion,
            precio=datos.precio,
            tipo=datos.tipo,
            especificaciones=datos.especificaciones,
            fotografias=datos.fotografias,
            **_construir(datos),
        )
        return self.repo.guardar(inmueble)


class BuscarInmuebles:
    """Estudiante.buscarInmuebles(filtros) del modelo V7."""

    def __init__(self, repo: RepositorioInmuebles):
        self.repo = repo

    def ejecutar(self, filtros: FiltrosInmueble) -> List[Inmueble]:
        if filtros.precio_min is not None and filtros.precio_max is not None and filtros.precio_min > filtros.precio_max:
            raise ErrorDominio("El mínimo no puede ser mayor que el máximo")
        return self.repo.buscar(filtros)


class ConsultarInmueble:
    def __init__(self, repo: RepositorioInmuebles):
        self.repo = repo

    def ejecutar(self, id_inmueble: int) -> Inmueble:
        inmueble = self.repo.buscar_por_id(id_inmueble)
        if not inmueble or inmueble.estado == EstadoInmueble.ELIMINADO:
            raise NoEncontrado("El inmueble no existe o ya no está publicado")
        return inmueble


class ListarMisInmuebles:
    def __init__(self, repo: RepositorioInmuebles):
        self.repo = repo

    def ejecutar(self, arrendador: Usuario) -> List[Inmueble]:
        if not arrendador.es_arrendador:
            raise NoAutorizado("Solo los arrendadores tienen inmuebles")
        return self.repo.listar_de_arrendador(arrendador.id_usuario)


class CambiarDisponibilidad:
    def __init__(self, repo: RepositorioInmuebles):
        self.repo = repo

    def ejecutar(self, arrendador: Usuario, id_inmueble: int, disponible: bool) -> Inmueble:
        inmueble = ConsultarInmueble(self.repo).ejecutar(id_inmueble)
        inmueble.verificar_dueno(arrendador.id_usuario)
        inmueble.actualizar_disponibilidad(disponible)
        return self.repo.guardar(inmueble)


def _construir(datos: DatosInmueble):
    return dict(
        ubicacion=Ubicacion(datos.direccion, datos.barrio, datos.latitud, datos.longitud),
        requisitos=[Requisito(r.strip()) for r in datos.requisitos if r.strip()],
    )


class ActualizarInmueble:
    def __init__(self, repo: RepositorioInmuebles):
        self.repo = repo

    def ejecutar(self, arrendador: Usuario, id_inmueble: int, datos: DatosInmueble) -> Inmueble:
        inmueble = ConsultarInmueble(self.repo).ejecutar(id_inmueble)
        inmueble.verificar_dueno(arrendador.id_usuario)
        partes = _construir(datos)
        inmueble.actualizar(datos.titulo, datos.descripcion, datos.precio, datos.tipo, partes["ubicacion"],
                            datos.especificaciones, datos.fotografias, partes["requisitos"])
        return self.repo.guardar(inmueble)


class EliminarInmueble:
    def __init__(self, repo: RepositorioInmuebles):
        self.repo = repo

    def ejecutar(self, arrendador: Usuario, id_inmueble: int) -> None:
        inmueble = ConsultarInmueble(self.repo).ejecutar(id_inmueble)
        inmueble.verificar_dueno(arrendador.id_usuario)
        inmueble.eliminar()
        self.repo.guardar(inmueble)
