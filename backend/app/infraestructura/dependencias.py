"""Raíz de composición: conecta cada puerto con su adaptador.

Es el único lugar que sabe que los repositorios son SQL, los tokens JWT y
la pasarela es Stripe (o la falsa en desarrollo).
"""
from typing import Iterator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.adaptadores.salida.pasarela_stripe import PasarelaFalsa, PasarelaStripe
from app.adaptadores.salida.repositorio_inmuebles_sql import RepositorioInmueblesSQL
from app.adaptadores.salida.repositorio_solicitudes_sql import (
    RepositorioPagosSQL, RepositorioReservasSQL, RepositorioSolicitudesSQL,
)
from app.adaptadores.salida.repositorio_usuarios_sql import RepositorioUsuariosSQL
from app.adaptadores.salida.seguridad import HasherBcrypt, ProveedorJWT
from app.dominio.usuario import Usuario
from app.puertos.pasarela import PasarelaPagos
from app.puertos.repositorios import (
    RepositorioInmuebles, RepositorioPagos, RepositorioReservas,
    RepositorioSolicitudes, RepositorioUsuarios,
)
from app.puertos.servicios import HasherContrasenas, ProveedorTokens

from .base_datos import FabricaSesiones
from .config import obtener_config

_bearer = HTTPBearer(auto_error=False)


def sesion_bd() -> Iterator[Session]:
    sesion = FabricaSesiones()
    try:
        yield sesion
    finally:
        sesion.close()


def repo_usuarios(s: Session = Depends(sesion_bd)) -> RepositorioUsuarios:
    return RepositorioUsuariosSQL(s)


def repo_inmuebles(s: Session = Depends(sesion_bd)) -> RepositorioInmuebles:
    return RepositorioInmueblesSQL(s)


def repo_solicitudes(s: Session = Depends(sesion_bd)) -> RepositorioSolicitudes:
    return RepositorioSolicitudesSQL(s)


def repo_reservas(s: Session = Depends(sesion_bd)) -> RepositorioReservas:
    return RepositorioReservasSQL(s)


def repo_pagos(s: Session = Depends(sesion_bd)) -> RepositorioPagos:
    return RepositorioPagosSQL(s)


def hasher() -> HasherContrasenas:
    return HasherBcrypt()


def tokens() -> ProveedorTokens:
    c = obtener_config()
    return ProveedorJWT(c.jwt_secret, c.jwt_minutos)


def pasarela() -> PasarelaPagos:
    c = obtener_config()
    if c.stripe_secret_key:
        return PasarelaStripe(c.stripe_secret_key, c.stripe_webhook_secret, c.stripe_url_exito, c.stripe_url_cancelar)
    return PasarelaFalsa(c.url_publica)


def usuario_actual(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    repo: RepositorioUsuarios = Depends(repo_usuarios),
    proveedor: ProveedorTokens = Depends(tokens),
) -> Usuario:
    id_usuario = proveedor.leer(cred.credentials) if cred else None
    usuario = repo.buscar_por_id(id_usuario) if id_usuario else None
    if not usuario:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tu sesión expiró. Inicia sesión de nuevo.")
    return usuario
