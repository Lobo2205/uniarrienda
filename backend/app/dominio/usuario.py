"""Entidad Usuario del modelo V7 (Estudiante y Arrendador se distinguen por el rol)."""
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .errores import ErrorDominio


class Rol(str, Enum):
    ESTUDIANTE = "estudiante"
    ARRENDADOR = "arrendador"
    ADMINISTRADOR = "administrador"  # fuera del MVP


@dataclass
class Usuario:
    nombre: str
    correo: str
    contrasena_hash: str
    telefono: str
    rol: Rol
    universidad: Optional[str] = None  # solo Estudiante
    id_usuario: Optional[int] = None

    def __post_init__(self) -> None:
        self.nombre = self.nombre.strip()
        self.correo = self.correo.strip().lower()
        if not self.nombre:
            raise ErrorDominio("El nombre es obligatorio")
        if self.rol == Rol.ESTUDIANTE and not (self.universidad or "").strip():
            raise ErrorDominio("El estudiante debe indicar su universidad")
        if self.rol != Rol.ESTUDIANTE:
            self.universidad = None

    @property
    def es_arrendador(self) -> bool:
        return self.rol == Rol.ARRENDADOR

    @property
    def es_estudiante(self) -> bool:
        return self.rol == Rol.ESTUDIANTE

    def actualizar_perfil(self, nombre: str, telefono: str, universidad: Optional[str]) -> None:
        self.nombre = nombre.strip() or self.nombre
        self.telefono = telefono.strip() or self.telefono
        if self.es_estudiante and universidad:
            self.universidad = universidad.strip()
