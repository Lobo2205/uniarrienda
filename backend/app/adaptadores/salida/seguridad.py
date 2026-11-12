"""Adaptadores de salida para contraseñas (bcrypt) y tokens (JWT)."""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt

from app.puertos.servicios import HasherContrasenas, ProveedorTokens


class HasherBcrypt(HasherContrasenas):
    def cifrar(self, contrasena: str) -> str:
        return bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()

    def verificar(self, contrasena: str, cifrada: str) -> bool:
        try:
            return bcrypt.checkpw(contrasena.encode(), cifrada.encode())
        except ValueError:
            return False


class ProveedorJWT(ProveedorTokens):
    def __init__(self, secreto: str, minutos: int):
        self.secreto, self.minutos = secreto, minutos

    def crear(self, id_usuario: int, rol: str) -> str:
        exp = datetime.now(timezone.utc) + timedelta(minutes=self.minutos)
        return jwt.encode({"sub": str(id_usuario), "rol": rol, "exp": exp}, self.secreto, algorithm="HS256")

    def leer(self, token: str) -> Optional[int]:
        try:
            return int(jwt.decode(token, self.secreto, algorithms=["HS256"])["sub"])
        except (jwt.PyJWTError, KeyError, ValueError):
            return None
