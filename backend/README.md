# UniArrienda · Backend (FastAPI + arquitectura hexagonal)

## Cómo está organizado

```
app/
├── dominio/            1. Entidades y reglas del negocio (modelo V7). Python puro.
│   ├── usuario.py         Usuario, Rol (estudiante / arrendador)
│   ├── inmueble.py        Inmueble, Ubicacion, Fotografia, Requisito, Especificaciones
│   ├── solicitud.py       Solicitud, Reserva, Pago (y sus estados)
│   └── errores.py         Errores del negocio
├── aplicacion/         2. Casos de uso: lo que la app sabe hacer
│   ├── usuarios.py        RegistrarUsuario, IniciarSesion, ConsultarPerfil, ActualizarPerfil
│   ├── inmuebles.py       PublicarInmueble, BuscarInmuebles, ConsultarInmueble,
│   │                      ActualizarInmueble, CambiarDisponibilidad, EliminarInmueble,
│   │                      ListarMisInmuebles
│   ├── solicitudes.py     CrearSolicitud, ListarMisSolicitudes, ListarSolicitudesDelArrendador,
│   │                      CancelarSolicitud, AprobarSolicitud, RechazarSolicitud,
│   │                      ConsultarReserva, CancelarReserva
│   └── pagos.py           IniciarPago, ConsultarEstadoPago, ProcesarEventoPago (webhook)
├── puertos/            3. Contratos (interfaces) que el núcleo necesita
│   ├── repositorios.py    RepositorioUsuarios, RepositorioInmuebles, RepositorioSolicitudes,
│   │                      RepositorioReservas, RepositorioPagos
│   ├── servicios.py       HasherContrasenas, ProveedorTokens
│   └── pasarela.py        PasarelaPagos
├── adaptadores/
│   ├── entrada/        4. API REST con FastAPI (la usan Flutter y React)
│   └── salida/         5. PostgreSQL, bcrypt, JWT y Stripe: implementan los puertos
├── infraestructura/    6. Configuración, conexión a la BD, raíz de composición, datos de ejemplo
└── main.py             Arranque de la API
```

**Regla de oro:** las flechas solo apuntan hacia adentro. `dominio` no importa nada de afuera;
`aplicacion` solo conoce `dominio` y `puertos`; los adaptadores conocen los puertos.
El único archivo que une puertos con adaptadores es `infraestructura/dependencias.py`.

## Puesta en marcha (Windows)

Desde la carpeta `backend`:

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Abre `.env` y cambia `TU_CLAVE` por la contraseña de tu usuario `postgres`. Luego:

```bat
python -m app.infraestructura.semilla
uvicorn app.main:app --reload --host 0.0.0.0
```

- Documentación interactiva: http://localhost:8000/docs
- Usuarios de ejemplo (contraseña `clave1234`): `laura@uniarrienda.co` (estudiante),
  `carlos@uniarrienda.co` y `marta@uniarrienda.co` (arrendadores).

Las tablas se crean solas al arrancar. Pruebas automáticas: `pytest -q`.

## Pagos con Stripe

Por defecto el backend usa una **pasarela falsa** para desarrollo: al "pagar", abres la URL que
devuelve `iniciar-pago` y el pago se marca como aprobado. Así puedes probar todo el flujo sin
cuenta de Stripe.

Para usar Stripe real (modo prueba), agrega a `.env`:

```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

Para que Stripe pueda llamar al webhook en desarrollo, usa `stripe listen --forward-to localhost:8000/pagos/webhook`.

## Endpoints

### Día 1 · Usuarios e inmuebles

| Método | Ruta | Pantalla | Quién |
| --- | --- | --- | --- |
| POST | /auth/registro | C04 | Público |
| POST | /auth/login | C03 | Público |
| GET / PUT | /usuarios/yo | E14, E15, A19, A20 | Con sesión |
| GET | /inmuebles?texto&tipo&precio_min&precio_max&barrio&wifi&mascotas | E01, E02, E03 | Público |
| GET | /inmuebles/{id} | E04 | Público |
| GET | /inmuebles/mios | A10 | Arrendador |
| POST | /inmuebles | A02–A09 | Arrendador |
| PUT | /inmuebles/{id} | A12 | Dueño |
| PATCH | /inmuebles/{id}/disponibilidad | A11 | Dueño |
| DELETE | /inmuebles/{id} | A11 | Dueño |
| POST | /fotos | A02 | Arrendador |

### Día 2 · Solicitud, reserva y pago

| Método | Ruta | Pantalla | Quién |
| --- | --- | --- | --- |
| POST | /solicitudes | E09 | Estudiante |
| GET | /solicitudes/mias | E10 | Estudiante |
| GET | /solicitudes/recibidas | A13 | Arrendador |
| POST | /solicitudes/{id}/cancelar | E11 | Estudiante dueño |
| POST | /solicitudes/{id}/aprobar | A14 | Arrendador dueño del inmueble |
| POST | /solicitudes/{id}/rechazar | A14 | Arrendador dueño del inmueble |
| GET | /reservas/{id} | E12, A15 | Estudiante o arrendador de la reserva |
| POST | /reservas/{id}/cancelar | E12, A15 | Estudiante o arrendador |
| POST | /reservas/{id}/iniciar-pago | A15 | Arrendador dueño |
| POST | /pagos/webhook | (interno) | Stripe |

Las rutas con sesión llevan el encabezado `Authorization: Bearer <token>`.

## Reglas clave del Día 2

- **Una Solicitud aprobada crea automáticamente una Reserva** y deja un Pago en estado `sin_iniciar`.
- **El arrendador** inicia el pago; el estudiante solo consulta el estado.
- Cuando el pago se aprueba (webhook): `Pago → aprobado`, `Reserva → confirmada`, `Inmueble.disponibilidad = false`.
- No se puede solicitar dos veces el mismo inmueble mientras la solicitud siga activa.
- No se puede cancelar una reserva con el pago ya aprobado.
