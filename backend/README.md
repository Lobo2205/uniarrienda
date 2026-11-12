# UniArrienda · Backend (FastAPI + arquitectura hexagonal)

## Cómo está organizado

```
app/
├── dominio/            1. Entidades y reglas del negocio (modelo V7). Python puro.
│   ├── usuario.py         Usuario, Rol (estudiante / arrendador)
│   ├── inmueble.py        Inmueble, Ubicacion, Fotografia, Requisito, Especificaciones
│   └── errores.py         Errores del negocio
├── aplicacion/         2. Casos de uso: lo que la app sabe hacer
│   ├── usuarios.py        RegistrarUsuario, IniciarSesion, ConsultarPerfil, ActualizarPerfil
│   └── inmuebles.py       PublicarInmueble, BuscarInmuebles, ConsultarInmueble, ActualizarInmueble,
│                          CambiarDisponibilidad, EliminarInmueble, ListarMisInmuebles
├── puertos/            3. Contratos (interfaces) que el núcleo necesita
│   ├── repositorios.py    RepositorioUsuarios, RepositorioInmuebles
│   └── servicios.py       HasherContrasenas, ProveedorTokens
├── adaptadores/
│   ├── entrada/        4. API REST con FastAPI (la usan Flutter y React)
│   └── salida/         5. PostgreSQL (SQLAlchemy), bcrypt y JWT: implementan los puertos
├── infraestructura/    6. Configuración, conexión a la BD, raíz de composición y datos de ejemplo
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

## Endpoints del Día 1

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

Las rutas con sesión llevan el encabezado `Authorization: Bearer <token>`.
