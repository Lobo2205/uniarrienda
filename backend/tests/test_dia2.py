"""Pruebas del Día 2: Solicitud, Reserva, Pago (con pasarela falsa)."""
from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)
INMUEBLE = {
    "titulo": "Habitación en Chapinero", "descripcion": "Con baño privado", "precio": 850000, "tipo": "habitacion",
    "direccion": "Calle 57 # 9-30", "barrio": "Chapinero",
    "especificaciones": {"habitaciones": 1, "banos": 1, "wifi": True},
    "fotografias": [{"url": "https://picsum.photos/seed/x/800/600", "espacio": "sala"}],
    "requisitos": ["Certificado de estudiante activo"],
}


def registrar(correo, rol, universidad=None):
    r = cliente.post("/auth/registro", json={"nombre": "Prueba", "correo": correo, "contrasena": "clave1234",
                                             "telefono": "3001234567", "rol": rol, "universidad": universidad})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_flujo_solicitud_reserva_pago():
    arr = registrar("arr2@test.co", "arrendador")
    est = registrar("est2@test.co", "estudiante", "Universidad Nacional")
    otro = registrar("otro2@test.co", "estudiante", "Universidad Nacional")

    # Crear inmueble
    inm = cliente.post("/inmuebles", json=INMUEBLE, headers=arr).json()
    id_inm = inm["id_inmueble"]

    # Reglas: arrendador no puede solicitar su propio inmueble, estudiante sí
    assert cliente.post("/solicitudes", json={"inmueble_id": id_inm}, headers=arr).status_code == 403
    assert cliente.post("/solicitudes", json={"inmueble_id": 99999}, headers=est).status_code == 404

    r = cliente.post("/solicitudes", json={"inmueble_id": id_inm}, headers=est)
    assert r.status_code == 201, r.text
    id_sol = r.json()["id_solicitud"]

    # No se puede solicitar dos veces lo mismo
    assert cliente.post("/solicitudes", json={"inmueble_id": id_inm}, headers=est).status_code == 409

    # Otro estudiante sí puede solicitarlo también
    r_otro = cliente.post("/solicitudes", json={"inmueble_id": id_inm}, headers=otro)
    assert r_otro.status_code == 201
    id_sol_otro = r_otro.json()["id_solicitud"]

    # El estudiante ve la suya y el arrendador ve las dos
    assert len(cliente.get("/solicitudes/mias", headers=est).json()) == 1
    assert len(cliente.get("/solicitudes/recibidas", headers=arr).json()) == 2

    # Solo el arrendador dueño aprueba
    assert cliente.post(f"/solicitudes/{id_sol}/aprobar", json={"fecha_inicio": "2027-01-15T00:00:00"},
                       headers=est).status_code == 403

    # Aprobar genera Reserva
    r = cliente.post(f"/solicitudes/{id_sol}/aprobar", json={"fecha_inicio": "2027-01-15T00:00:00"}, headers=arr)
    assert r.status_code == 201
    id_reserva = r.json()["id_reserva"]
    assert r.json()["monto"] == 850000 and r.json()["estado"] == "activa"

    # El estudiante ve la reserva y el pago
    rp = cliente.get(f"/reservas/{id_reserva}", headers=est).json()
    assert rp["pago"]["estado"] == "sin_iniciar" and rp["pago"]["monto"] == 850000
    assert cliente.get(f"/reservas/{id_reserva}", headers=registrar("ajeno@test.co", "estudiante", "UN")).status_code == 403

    # Estudiante NO puede iniciar pago (lo inicia el arrendador)
    assert cliente.post(f"/reservas/{id_reserva}/iniciar-pago", headers=est).status_code == 403

    # Arrendador inicia pago -> pasarela falsa devuelve URL
    r = cliente.post(f"/reservas/{id_reserva}/iniciar-pago", headers=arr)
    assert r.status_code == 200
    datos = r.json()
    assert datos["url_pago"].endswith(f"referencia={datos['referencia']}")

    # Pago queda pendiente
    rp = cliente.get(f"/reservas/{id_reserva}", headers=est).json()
    assert rp["pago"]["estado"] == "pendiente"

    # Simular el pago entrando a la URL falsa
    r = cliente.get(datos["url_pago"].replace("http://localhost:8000", ""))
    assert r.status_code == 200 and r.json()["aprobado"] is True

    # Pago aprobado, reserva confirmada, inmueble no disponible
    rp = cliente.get(f"/reservas/{id_reserva}", headers=est).json()
    assert rp["pago"]["estado"] == "aprobado"
    assert rp["reserva"]["estado"] == "confirmada"
    assert cliente.get(f"/inmuebles/{id_inm}").json()["disponibilidad"] is False
    # Ya no se puede solicitar
    assert cliente.get("/inmuebles").json() == []

    # El otro estudiante cancela la suya (seguía pendiente)
    r = cliente.post(f"/solicitudes/{id_sol_otro}/cancelar", headers=otro)
    assert r.status_code == 200 and r.json()["estado"] == "cancelada"
    assert cliente.post(f"/solicitudes/{id_sol_otro}/cancelar", headers=otro).status_code == 400


def test_rechazo_y_cancelacion_reserva():
    arr = registrar("arr3@test.co", "arrendador")
    est = registrar("est3@test.co", "estudiante", "UN")
    inm = cliente.post("/inmuebles", json=INMUEBLE, headers=arr).json()
    sol = cliente.post("/solicitudes", json={"inmueble_id": inm["id_inmueble"]}, headers=est).json()
    r = cliente.post(f"/solicitudes/{sol['id_solicitud']}/rechazar", headers=arr)
    assert r.status_code == 200 and r.json()["estado"] == "rechazada"
    # Cancelar reserva activa
    sol2 = cliente.post("/solicitudes", json={"inmueble_id": inm["id_inmueble"]}, headers=est).json()
    res = cliente.post(f"/solicitudes/{sol2['id_solicitud']}/aprobar",
                       json={"fecha_inicio": "2027-02-01T00:00:00"}, headers=arr).json()
    r = cliente.post(f"/reservas/{res['id_reserva']}/cancelar", headers=est)
    assert r.status_code == 200 and r.json()["estado"] == "cancelada"
