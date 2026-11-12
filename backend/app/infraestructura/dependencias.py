"""Raíz de composición: conecta cada puerto con su adaptador.

Es el único lugar que sabe que los repositorios son SQL y que los tokens son JWT.
Si mañana cambia la tecnología, solo se cambia este archivo.
"""
from typing import Iterator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.adaptadores.salida.repositorio_inmuebles_sql import RepositorioInmueblesSQL
from app.adaptadores.salida.repositorio_usuarios_sql import RepositorioUsuariosSQL
from app.adaptadores.salida.seguridad import HasherBcrypt, ProveedorJWT
from app.dominio.usuario import Usuario
from app.puertos.repositorios import RepositorioInmuebles, RepositorioUsuarios
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


def hasher() -> HasherContrasenas:
    return HasherBcrypt()


def tokens() -> ProveedorTokens:
    c = obtener_config()
    return ProveedorJWT(c.jwt_secret, c.jwt_minutos)


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
