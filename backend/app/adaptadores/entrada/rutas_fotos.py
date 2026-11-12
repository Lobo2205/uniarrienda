"""Adaptador de entrada: subir fotos de inmuebles. Devuelve la URL para usarla al publicar."""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.dominio.usuario import Usuario
from app.infraestructura.config import obtener_config
from app.infraestructura.dependencias import usuario_actual

router = APIRouter(prefix="/fotos", tags=["Fotos"])
PERMITIDOS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_BYTES = 5 * 1024 * 1024


@router.post("", status_code=status.HTTP_201_CREATED)
async def subir_foto(archivo: UploadFile, yo: Usuario = Depends(usuario_actual)):
    if not yo.es_arrendador:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo los arrendadores suben fotos")
    extension = PERMITIDOS.get(archivo.content_type or "")
    if not extension:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Formato no permitido. Usa JPG, PNG o WEBP")
    contenido = await archivo.read()
    if len(contenido) > MAX_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La foto supera 5 MB")
    config = obtener_config()
    carpeta = Path(config.carpeta_media)
    carpeta.mkdir(parents=True, exist_ok=True)
    nombre = f"{uuid.uuid4().hex}{extension}"
    (carpeta / nombre).write_bytes(contenido)
    return {"url": f"{config.url_publica.rstrip('/')}/media/{nombre}"}
