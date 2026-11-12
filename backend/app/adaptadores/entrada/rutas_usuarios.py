"""Adaptador de entrada: endpoints de autenticación y perfil."""
from fastapi import APIRouter, Depends, status

from app.aplicacion.usuarios import (
    ActualizarPerfil, DatosRegistro, IniciarSesion, RegistrarUsuario,
)
from app.dominio.usuario import Usuario
from app.infraestructura.dependencias import hasher, repo_usuarios, tokens, usuario_actual

from .esquemas import LoginEntrada, PerfilEntrada, RegistroEntrada, SesionSalida, UsuarioSalida

router = APIRouter(tags=["Usuarios"])


@router.post("/auth/registro", response_model=SesionSalida, status_code=status.HTTP_201_CREATED)
def registrar(datos: RegistroEntrada, repo=Depends(repo_usuarios), h=Depends(hasher), t=Depends(tokens)):
    usuario = RegistrarUsuario(repo, h).ejecutar(DatosRegistro(**datos.model_dump()))
    token = t.crear(usuario.id_usuario, usuario.rol.value)
    return SesionSalida(token=token, usuario=UsuarioSalida.desde(usuario))


@router.post("/auth/login", response_model=SesionSalida)
def iniciar_sesion(datos: LoginEntrada, repo=Depends(repo_usuarios), h=Depends(hasher), t=Depends(tokens)):
    token, usuario = IniciarSesion(repo, h, t).ejecutar(datos.correo, datos.contrasena)
    return SesionSalida(token=token, usuario=UsuarioSalida.desde(usuario))


@router.get("/usuarios/yo", response_model=UsuarioSalida)
def consultar_perfil(yo: Usuario = Depends(usuario_actual)):
    return UsuarioSalida.desde(yo)


@router.put("/usuarios/yo", response_model=UsuarioSalida)
def actualizar_perfil(datos: PerfilEntrada, yo: Usuario = Depends(usuario_actual), repo=Depends(repo_usuarios)):
    usuario = ActualizarPerfil(repo).ejecutar(yo.id_usuario, datos.nombre, datos.telefono, datos.universidad)
    return UsuarioSalida.desde(usuario)
