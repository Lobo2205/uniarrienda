"""Adaptador de salida: implementa RepositorioUsuarios con PostgreSQL."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dominio.usuario import Rol, Usuario
from app.puertos.repositorios import RepositorioUsuarios

from .modelos_orm import UsuarioORM


def _a_dominio(f: UsuarioORM) -> Usuario:
    return Usuario(nombre=f.nombre, correo=f.correo, contrasena_hash=f.contrasena, telefono=f.telefono,
                   rol=Rol(f.rol), universidad=f.universidad, id_usuario=f.id_usuario)


class RepositorioUsuariosSQL(RepositorioUsuarios):
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def guardar(self, usuario: Usuario) -> Usuario:
        fila = self.sesion.get(UsuarioORM, usuario.id_usuario) if usuario.id_usuario else UsuarioORM()
        fila.nombre, fila.correo, fila.contrasena = usuario.nombre, usuario.correo, usuario.contrasena_hash
        fila.telefono, fila.rol, fila.universidad = usuario.telefono, usuario.rol.value, usuario.universidad
        self.sesion.add(fila)
        self.sesion.commit()
        return _a_dominio(fila)

    def buscar_por_correo(self, correo: str) -> Optional[Usuario]:
        fila = self.sesion.scalar(select(UsuarioORM).where(UsuarioORM.correo == correo))
        return _a_dominio(fila) if fila else None

    def buscar_por_id(self, id_usuario: int) -> Optional[Usuario]:
        fila = self.sesion.get(UsuarioORM, id_usuario)
        return _a_dominio(fila) if fila else None
