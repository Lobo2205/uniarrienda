"""Formatos JSON de entrada y salida de la API (Pydantic). Traducen entre HTTP y el dominio."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.dominio.inmueble import Especificaciones, Fotografia, Inmueble, TipoInmueble
from app.dominio.usuario import Rol, Usuario


# ---------- Usuarios ----------
class RegistroEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    correo: EmailStr
    contrasena: str = Field(min_length=8, max_length=72)
    telefono: str = Field(min_length=7, max_length=30)
    rol: Rol
    universidad: Optional[str] = None


class LoginEntrada(BaseModel):
    correo: EmailStr
    contrasena: str


class PerfilEntrada(BaseModel):
    nombre: str = ""
    telefono: str = ""
    universidad: Optional[str] = None


class UsuarioSalida(BaseModel):
    id_usuario: int
    nombre: str
    correo: str
    telefono: str
    rol: Rol
    universidad: Optional[str]

    @classmethod
    def desde(cls, u: Usuario) -> "UsuarioSalida":
        return cls(id_usuario=u.id_usuario, nombre=u.nombre, correo=u.correo, telefono=u.telefono,
                   rol=u.rol, universidad=u.universidad)


class SesionSalida(BaseModel):
    token: str
    usuario: UsuarioSalida


# ---------- Inmuebles ----------
class FotografiaEsquema(BaseModel):
    url: str
    espacio: str = "general"


class EspecificacionesEsquema(BaseModel):
    habitaciones: int = Field(1, ge=0, le=20)
    banos: int = Field(1, ge=0, le=20)
    cocina: bool = False
    estacionamiento: bool = False
    mascotas: bool = False
    wifi: bool = False
    servicios_incluidos: bool = False


class InmuebleEntrada(BaseModel):
    titulo: str = Field(min_length=3, max_length=160)
    descripcion: str = ""
    precio: int = Field(gt=0)
    tipo: TipoInmueble
    direccion: str = Field(min_length=3)
    barrio: str = Field(min_length=2)
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    especificaciones: EspecificacionesEsquema = EspecificacionesEsquema()
    fotografias: List[FotografiaEsquema] = Field(min_length=1)
    requisitos: List[str] = []

    def a_datos(self):
        from app.aplicacion.inmuebles import DatosInmueble
        return DatosInmueble(
            titulo=self.titulo, descripcion=self.descripcion, precio=self.precio, tipo=self.tipo,
            direccion=self.direccion, barrio=self.barrio, latitud=self.latitud, longitud=self.longitud,
            especificaciones=Especificaciones(**self.especificaciones.model_dump()),
            fotografias=[Fotografia(f.url, f.espacio) for f in self.fotografias],
            requisitos=self.requisitos,
        )


class DisponibilidadEntrada(BaseModel):
    disponible: bool


class UbicacionSalida(BaseModel):
    direccion: str
    barrio: str
    latitud: Optional[float]
    longitud: Optional[float]


class InmuebleSalida(BaseModel):
    id_inmueble: int
    arrendador_id: int
    titulo: str
    descripcion: str
    precio: int
    tipo: TipoInmueble
    disponibilidad: bool
    estado: str
    fecha_publicacion: datetime
    ubicacion: UbicacionSalida
    especificaciones: EspecificacionesEsquema
    fotografias: List[FotografiaEsquema]
    requisitos: List[str]

    @classmethod
    def desde(cls, i: Inmueble) -> "InmuebleSalida":
        u, e = i.ubicacion, i.especificaciones
        return cls(
            id_inmueble=i.id_inmueble, arrendador_id=i.arrendador_id, titulo=i.titulo, descripcion=i.descripcion,
            precio=i.precio, tipo=i.tipo, disponibilidad=i.disponibilidad, estado=i.estado.value,
            fecha_publicacion=i.fecha_publicacion,
            ubicacion=UbicacionSalida(direccion=u.direccion, barrio=u.barrio, latitud=u.latitud, longitud=u.longitud),
            especificaciones=EspecificacionesEsquema(**e.__dict__),
            fotografias=[FotografiaEsquema(url=f.url, espacio=f.espacio) for f in i.fotografias],
            requisitos=[r.descripcion for r in i.requisitos],
        )


class ArrendadorPublico(BaseModel):
    """Perfil de anfitrión: nombre y teléfono del Usuario (Arrendador no tiene atributos propios)."""
    id_usuario: int
    nombre: str
    telefono: str


class InmuebleDetalleSalida(InmuebleSalida):
    arrendador: Optional[ArrendadorPublico] = None
