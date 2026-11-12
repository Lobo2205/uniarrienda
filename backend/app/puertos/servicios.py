"""Puertos para servicios técnicos que el negocio usa sin conocer su implementación."""
from abc import ABC, abstractmethod
from typing import Optional


class HasherContrasenas(ABC):
    @abstractmethod
    def cifrar(self, contrasena: str) -> str: ...

    @abstractmethod
    def verificar(self, contrasena: str, cifrada: str) -> bool: ...


class ProveedorTokens(ABC):
    @abstractmethod
    def crear(self, id_usuario: int, rol: str) -> str: ...

    @abstractmethod
    def leer(self, token: str) -> Optional[int]:
        """Devuelve el id del usuario o None si el token no es válido."""
