"""Carga datos de ejemplo para probar las apps.  Uso:  python -m app.infraestructura.semilla"""
from app.adaptadores.salida.repositorio_inmuebles_sql import RepositorioInmueblesSQL
from app.adaptadores.salida.repositorio_usuarios_sql import RepositorioUsuariosSQL
from app.adaptadores.salida.seguridad import HasherBcrypt
from app.aplicacion.inmuebles import DatosInmueble, PublicarInmueble
from app.aplicacion.usuarios import DatosRegistro, RegistrarUsuario
from app.dominio.inmueble import Especificaciones, Fotografia, TipoInmueble
from app.dominio.usuario import Rol

from .base_datos import FabricaSesiones, crear_tablas

CLAVE = "clave1234"


def foto(semilla: str, espacio: str) -> Fotografia:
    return Fotografia(f"https://picsum.photos/seed/{semilla}/800/600", espacio)


INMUEBLES = [
    ("Habitación en Chapinero", 850000, TipoInmueble.HABITACION, "Chapinero", "Calle 57 # 9-30", 4.6436, -74.0638,
     Especificaciones(1, 1, True, False, True, True, True), ["Certificado de estudiante activo", "Codeudor o depósito de un mes"]),
    ("Apartaestudio amoblado", 1150000, TipoInmueble.APARTAESTUDIO, "Chapinero", "Carrera 13 # 63-20", 4.6489, -74.0640,
     Especificaciones(1, 1, True, False, False, True, False), ["Contrato mínimo de 6 meses"]),
    ("Apartamento en Teusaquillo", 1400000, TipoInmueble.APARTAMENTO, "Teusaquillo", "Calle 39 # 20-15", 4.6280, -74.0730,
     Especificaciones(2, 1, True, True, True, True, False), ["Codeudor", "No fumar dentro del inmueble"]),
    ("Habitación cerca a la Nacional", 700000, TipoInmueble.HABITACION, "Teusaquillo", "Carrera 30 # 45-10", 4.6360, -74.0820,
     Especificaciones(1, 1, False, False, False, True, True), ["Certificado de estudiante activo"]),
    ("Habitación en La Candelaria", 650000, TipoInmueble.HABITACION, "La Candelaria", "Calle 12 # 3-40", 4.5970, -74.0710,
     Especificaciones(1, 1, True, False, False, False, True), ["Depósito de un mes"]),
    ("Casa compartida para estudiantes", 900000, TipoInmueble.CASA, "Galerías", "Calle 53 # 24-60", 4.6450, -74.0760,
     Especificaciones(4, 2, True, True, True, True, True), ["Certificado de estudiante activo", "Convivencia responsable"]),
]


def cargar() -> None:
    crear_tablas()
    sesion = FabricaSesiones()
    try:
        usuarios, inmuebles = RepositorioUsuariosSQL(sesion), RepositorioInmueblesSQL(sesion)
        if usuarios.buscar_por_correo("carlos@uniarrienda.co"):
            print("Los datos de ejemplo ya estaban cargados.")
            return
        registrar = RegistrarUsuario(usuarios, HasherBcrypt())
        registrar.ejecutar(DatosRegistro("Laura Gómez", "laura@uniarrienda.co", CLAVE, "3001112233", Rol.ESTUDIANTE, "Universidad Nacional"))
        carlos = registrar.ejecutar(DatosRegistro("Carlos Pérez", "carlos@uniarrienda.co", CLAVE, "3004445566", Rol.ARRENDADOR))
        marta = registrar.ejecutar(DatosRegistro("Marta Ruiz", "marta@uniarrienda.co", CLAVE, "3007778899", Rol.ARRENDADOR))
        publicar = PublicarInmueble(inmuebles)
        for n, (titulo, precio, tipo, barrio, dir_, lat, lng, esp, req) in enumerate(INMUEBLES):
            datos = DatosInmueble(
                titulo=titulo, precio=precio, tipo=tipo, barrio=barrio, direccion=dir_, latitud=lat, longitud=lng,
                descripcion=f"{titulo} con buena iluminación, cerca de transporte público y universidades.",
                especificaciones=esp, requisitos=req,
                fotografias=[foto(f"ua{n}a", "habitación"), foto(f"ua{n}b", "baño"), foto(f"ua{n}c", "sala")],
            )
            publicar.ejecutar(carlos if n % 2 == 0 else marta, datos)
        print("Listo: 1 estudiante, 2 arrendadores y 6 inmuebles. Contraseña de todos:", CLAVE)
    finally:
        sesion.close()


if __name__ == "__main__":
    cargar()
