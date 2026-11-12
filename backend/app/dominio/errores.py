"""Errores del negocio. No dependen de FastAPI ni de la base de datos."""


class ErrorDominio(Exception):
    """Regla del negocio incumplida (datos inválidos, estado no permitido)."""


class NoEncontrado(ErrorDominio):
    """El recurso pedido no existe."""


class NoAutorizado(ErrorDominio):
    """El usuario no tiene permiso para esta acción."""


class Conflicto(ErrorDominio):
    """El recurso ya existe o cambió de estado (por ejemplo, correo ya registrado)."""
