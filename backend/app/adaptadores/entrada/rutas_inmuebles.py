"""Adaptador de entrada: endpoints de inmuebles."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status

from app.aplicacion.inmuebles import (
    ActualizarInmueble, BuscarInmuebles, CambiarDisponibilidad, ConsultarInmueble,
    EliminarInmueble, ListarMisInmuebles, PublicarInmueble,
)
from app.dominio.inmueble import TipoInmueble
from app.dominio.usuario import Usuario
from app.infraestructura.dependencias import repo_inmuebles, repo_usuarios, usuario_actual
from app.puertos.repositorios import FiltrosInmueble

from .esquemas import (
    ArrendadorPublico, DisponibilidadEntrada, InmuebleDetalleSalida, InmuebleEntrada, InmuebleSalida,
)

router = APIRouter(prefix="/inmuebles", tags=["Inmuebles"])


@router.get("", response_model=List[InmuebleSalida])
def buscar(
    texto: Optional[str] = None,
    tipo: Optional[TipoInmueble] = None,
    precio_min: Optional[int] = Query(None, ge=0),
    precio_max: Optional[int] = Query(None, ge=0),
    barrio: Optional[str] = None,
    wifi: Optional[bool] = None,
    mascotas: Optional[bool] = None,
    repo=Depends(repo_inmuebles),
):
    """Búsqueda pública con filtros (pantallas E01, E02, E03)."""
    filtros = FiltrosInmueble(texto=texto, tipo=tipo, precio_min=precio_min, precio_max=precio_max,
                              barrio=barrio, wifi=wifi, mascotas=mascotas)
    return [InmuebleSalida.desde(i) for i in BuscarInmuebles(repo).ejecutar(filtros)]


@router.get("/mios", response_model=List[InmuebleSalida])
def mis_inmuebles(yo: Usuario = Depends(usuario_actual), repo=Depends(repo_inmuebles)):
    """Inmuebles del arrendador que inició sesión (A10)."""
    return [InmuebleSalida.desde(i) for i in ListarMisInmuebles(repo).ejecutar(yo)]


@router.get("/{id_inmueble}", response_model=InmuebleDetalleSalida)
def detalle(id_inmueble: int, repo=Depends(repo_inmuebles), repo_u=Depends(repo_usuarios)):
    """Detalle con perfil de anfitrión (E04)."""
    inmueble = ConsultarInmueble(repo).ejecutar(id_inmueble)
    salida = InmuebleDetalleSalida(**InmuebleSalida.desde(inmueble).model_dump())
    dueno = repo_u.buscar_por_id(inmueble.arrendador_id)
    if dueno:
        salida.arrendador = ArrendadorPublico(id_usuario=dueno.id_usuario, nombre=dueno.nombre, telefono=dueno.telefono)
    return salida


@router.post("", response_model=InmuebleSalida, status_code=status.HTTP_201_CREATED)
def publicar(datos: InmuebleEntrada, yo: Usuario = Depends(usuario_actual), repo=Depends(repo_inmuebles)):
    """Publicar inmueble (A02 a A09)."""
    return InmuebleSalida.desde(PublicarInmueble(repo).ejecutar(yo, datos.a_datos()))


@router.put("/{id_inmueble}", response_model=InmuebleSalida)
def actualizar(id_inmueble: int, datos: InmuebleEntrada, yo: Usuario = Depends(usuario_actual), repo=Depends(repo_inmuebles)):
    """Editar inmueble (A12)."""
    return InmuebleSalida.desde(ActualizarInmueble(repo).ejecutar(yo, id_inmueble, datos.a_datos()))


@router.patch("/{id_inmueble}/disponibilidad", response_model=InmuebleSalida)
def cambiar_disponibilidad(id_inmueble: int, datos: DisponibilidadEntrada,
                           yo: Usuario = Depends(usuario_actual), repo=Depends(repo_inmuebles)):
    """Marcar disponible o no disponible (A11)."""
    return InmuebleSalida.desde(CambiarDisponibilidad(repo).ejecutar(yo, id_inmueble, datos.disponible))


@router.delete("/{id_inmueble}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(id_inmueble: int, yo: Usuario = Depends(usuario_actual), repo=Depends(repo_inmuebles)):
    """Eliminar inmueble (A11). Borrado lógico."""
    EliminarInmueble(repo).ejecutar(yo, id_inmueble)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
