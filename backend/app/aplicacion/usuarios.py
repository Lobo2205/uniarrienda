"""Casos de uso de Usuario: registrarse, iniciar sesión, consultar y actualizar perfil."""
from dataclasses import dataclass
from typing import Optional

from app.dominio.errores import Conflicto, ErrorDominio, NoAutorizado, NoEncontrado
from app.dominio.usuario import Rol, Usuario
from app.puertos.repositorios import RepositorioUsuarios
from app.puertos.servicios import HasherContrasenas, ProveedorTokens


@dataclass
class DatosRegistro:
    nombre: str
    correo: str
    contrasena: str
    telefono: str
    rol: Rol
    universidad: Optional[str] = None


class RegistrarUsuario:
    def __init__(self, repo: RepositorioUsuarios, hasher: HasherContrasenas):
        self.repo, self.hasher = repo, hasher

    def ejecutar(self, datos: DatosRegistro) -> Usuario:
        if datos.rol == Rol.ADMINISTRADOR:
            raise ErrorDominio("No se puede registrar un administrador desde la app")
        if len(datos.contrasena) < 8:
            raise ErrorDominio("La contraseña debe tener al menos 8 caracteres")
        if self.repo.buscar_por_correo(datos.correo.strip().lower()):
            raise Conflicto("Ese correo ya está registrado")
        usuario = Usuario(
            nombre=datos.nombre,
            correo=datos.correo,
            contrasena_hash=self.hasher.cifrar(datos.contrasena),
            telefono=datos.telefono,
            rol=datos.rol,
            universidad=datos.universidad,
        )
        return self.repo.guardar(usuario)


class IniciarSesion:
    def __init__(self, repo: RepositorioUsuarios, hasher: HasherContrasenas, tokens: ProveedorTokens):
        self.repo, self.hasher, self.tokens = repo, hasher, tokens

    def ejecutar(self, correo: str, contrasena: str) -> tuple[str, Usuario]:
        usuario = self.repo.buscar_por_correo(correo.strip().lower())
        if not usuario or not self.hasher.verificar(contrasena, usuario.contrasena_hash):
            raise NoAutorizado("Correo o contraseña incorrectos")
        return self.tokens.crear(usuario.id_usuario, usuario.rol.value), usuario


class ConsultarPerfil:
    def __init__(self, repo: RepositorioUsuarios):
        self.repo = repo

    def ejecutar(self, id_usuario: int) -> Usuario:
        usuario = self.repo.buscar_por_id(id_usuario)
        if not usuario:
            raise NoEncontrado("Usuario no encontrado")
        return usuario


class ActualizarPerfil:
    def __init__(self, repo: RepositorioUsuarios):
        self.repo = repo

    def ejecutar(self, id_usuario: int, nombre: str, telefono: str, universidad: Optional[str]) -> Usuario:
        usuario = ConsultarPerfil(self.repo).ejecutar(id_usuario)
        usuario.actualizar_perfil(nombre, telefono, universidad)
        return self.repo.guardar(usuario)
