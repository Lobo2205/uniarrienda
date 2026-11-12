"""Pruebas de punta a punta de la API del Día 1."""
from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)
INMUEBLE = {
    "titulo": "Habitación en Chapinero", "descripcion": "Con baño privado", "precio": 850000, "tipo": "habitacion",
    "direccion": "Calle 57 # 9-30", "barrio": "Chapinero",
    "especificaciones": {"habitaciones": 1, "banos": 1, "wifi": True, "mascotas": True},
    "fotografias": [{"url": "https://picsum.photos/seed/a/800/600", "espacio": "habitación"}],
    "requisitos": ["Certificado de estudiante activo", "  "],
}


def registrar(correo, rol, universidad=None):
    r = cliente.post("/auth/registro", json={"nombre": "Prueba", "correo": correo, "contrasena": "clave1234",
                                            "telefono": "3001234567", "rol": rol, "universidad": universidad})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_flujo_completo():
    arr = registrar("arr@test.co", "arrendador")
    est = registrar("est@test.co", "estudiante", "Universidad Nacional")

    # Registro duplicado y login
    assert cliente.post("/auth/registro", json={"nombre": "Otro", "correo": "ARR@test.co", "contrasena": "clave1234",
                                                "telefono": "3001234567", "rol": "arrendador"}).status_code == 409
    assert cliente.post("/auth/login", json={"correo": "arr@test.co", "contrasena": "mala-clave"}).status_code == 401
    assert cliente.post("/auth/login", json={"correo": "arr@test.co", "contrasena": "clave1234"}).status_code == 200
    assert cliente.get("/usuarios/yo").status_code == 401
    assert cliente.get("/usuarios/yo", headers=est).json()["universidad"] == "Universidad Nacional"

    # Publicar: estudiante no puede, arrendador sí
    assert cliente.post("/inmuebles", json=INMUEBLE, headers=est).status_code == 403
    r = cliente.post("/inmuebles", json=INMUEBLE, headers=arr)
    assert r.status_code == 201, r.text
    creado = r.json()
    assert creado["requisitos"] == ["Certificado de estudiante activo"]
    id_ = creado["id_inmueble"]

    # Buscar con filtros
    assert len(cliente.get("/inmuebles", params={"barrio": "chapi", "wifi": True}).json()) == 1
    assert cliente.get("/inmuebles", params={"precio_min": 900000}).json() == []
    assert cliente.get("/inmuebles", params={"precio_min": 2000, "precio_max": 1000}).status_code == 400

    # Detalle con anfitrión
    d = cliente.get(f"/inmuebles/{id_}").json()
    assert d["arrendador"]["nombre"] == "Prueba" and d["especificaciones"]["wifi"] is True

    # Editar, disponibilidad, mis inmuebles
    cambio = dict(INMUEBLE, precio=900000)
    assert cliente.put(f"/inmuebles/{id_}", json=cambio, headers=arr).json()["precio"] == 900000
    assert cliente.put(f"/inmuebles/{id_}", json=cambio, headers=est).status_code == 403
    assert cliente.patch(f"/inmuebles/{id_}/disponibilidad", json={"disponible": False}, headers=arr).json()["disponibilidad"] is False
    assert cliente.get("/inmuebles").json() == []          # oculto en búsquedas
    assert len(cliente.get("/inmuebles/mios", headers=arr).json()) == 1

    # Eliminar
    assert cliente.delete(f"/inmuebles/{id_}", headers=arr).status_code == 204
    assert cliente.get(f"/inmuebles/{id_}").status_code == 404
    assert cliente.get("/inmuebles/mios", headers=arr).json() == []


def test_subir_foto():
    arr = registrar("fotos@test.co", "arrendador")
    r = cliente.post("/fotos", headers=arr, files={"archivo": ("a.png", b"\x89PNG fake", "image/png")})
    assert r.status_code == 201 and r.json()["url"].endswith(".png")
    url = r.json()["url"].replace("http://localhost:8000", "")
    assert cliente.get(url).status_code == 200
    assert cliente.post("/fotos", headers=arr, files={"archivo": ("a.txt", b"x", "text/plain")}).status_code == 400
