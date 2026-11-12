"""Pruebas del núcleo: no usan base de datos ni FastAPI (así se ve la ventaja de la hexagonal)."""
import pytest

from app.dominio.errores import ErrorDominio, NoAutorizado
from app.dominio.inmueble import Fotografia, Inmueble, TipoInmueble, Ubicacion
from app.dominio.usuario import Rol, Usuario


def inmueble(**cambios):
    datos = dict(arrendador_id=1, titulo="Habitación", descripcion="", precio=800000, tipo=TipoInmueble.HABITACION,
                 ubicacion=Ubicacion("Calle 1", "Chapinero"), fotografias=[Fotografia("u", "sala")])
    datos.update(cambios)
    return Inmueble(**datos)


def test_precio_debe_ser_positivo():
    with pytest.raises(ErrorDominio):
        inmueble(precio=0)


def test_requiere_al_menos_una_foto():
    with pytest.raises(ErrorDominio):
        inmueble(fotografias=[])


def test_solo_el_dueno_modifica():
    with pytest.raises(NoAutorizado):
        inmueble().verificar_dueno(99)


def test_estudiante_requiere_universidad():
    with pytest.raises(ErrorDominio):
        Usuario("Ana", "a@a.co", "x", "300", Rol.ESTUDIANTE)


def test_arrendador_no_guarda_universidad():
    u = Usuario("Carlos", "C@A.CO", "x", "300", Rol.ARRENDADOR, universidad="UN")
    assert u.universidad is None and u.correo == "c@a.co"
