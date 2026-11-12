"""Punto de arranque de la API de UniArrienda."""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.adaptadores.entrada import rutas_fotos, rutas_inmuebles, rutas_usuarios
from app.dominio.errores import Conflicto, ErrorDominio, NoAutorizado, NoEncontrado
from app.infraestructura.base_datos import crear_tablas
from app.infraestructura.config import obtener_config

app = FastAPI(title="UniArrienda API", version="0.1.0",
              description="Backend con arquitectura hexagonal para la app de arriendos universitarios.")

# Permite que React (navegador) llame a la API. En producción se restringe al dominio real.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

crear_tablas()
carpeta_media = Path(obtener_config().carpeta_media)
carpeta_media.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=carpeta_media), name="media")

app.include_router(rutas_usuarios.router)
app.include_router(rutas_inmuebles.router)
app.include_router(rutas_fotos.router)


# Traduce los errores del dominio a respuestas HTTP con un mensaje claro: {"detail": "..."}
@app.exception_handler(ErrorDominio)
def manejar_error_dominio(_: Request, error: ErrorDominio):
    codigo = 400
    if isinstance(error, NoEncontrado):
        codigo = 404
    elif isinstance(error, NoAutorizado):
        codigo = 401 if "contraseña" in str(error) else 403
    elif isinstance(error, Conflicto):
        codigo = 409
    return JSONResponse(status_code=codigo, content={"detail": str(error)})


@app.get("/", tags=["Estado"])
def estado():
    return {"app": "UniArrienda API", "estado": "ok", "documentacion": "/docs"}
