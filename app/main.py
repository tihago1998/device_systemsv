import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.auth.auth_routes import router as auth_router
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, API_VERSION, APP_NAME, CORS_ORIGINS, RATE_LIMIT_ENABLED
from app.middlewares import rate_limit
from app.middlewares.request_middleware import RequestMiddleware
from app.routes.device_routes import router as device_router
from app.routes.loan_routes import router as loan_router
from app.routes.user_routes import router as user_router

# Muestra en consola el log de cada petición que registra RequestMiddleware
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# Las tablas ya no se crean aquí con create_all: la estructura de la base de datos
# se versiona con Alembic (alembic upgrade head).

tags_metadata = [
    {"name": "Auth", "description": "Registro, login con OAuth2 (token JWT) y datos del usuario autenticado."},
    {"name": "Users", "description": "Gestión de usuarios (requiere token). Crear, modificar y eliminar: solo admin."},
    {"name": "Devices", "description": "Equipos para préstamo. Consultar es público; crear/editar: admin o support; eliminar: admin."},
    {"name": "Loans", "description": "Préstamos de dispositivos (requiere token). Devoluciones y reportes: admin o support."},
    {"name": "Security", "description": "Estado de la API y configuración de seguridad (CORS, JWT, rate limiting)."},
]

app = FastAPI(
    title="device_systems API",
    description=(
        "API REST segura para gestión de usuarios, dispositivos y préstamos. "
        "Autenticación OAuth2 con JWT, contraseñas con hash bcrypt, autorización por roles, CORS, "
        "middleware de trazabilidad y rate limiting. Para probar las rutas protegidas use el botón "
        "**Authorize** (username = correo)."
    ),
    version=API_VERSION,
    contact={
        "name": "Santiago Varela Peña",
        "email": "santiago@example.com",
    },
    openapi_tags=tags_metadata,
)

# Rate limiting (slowapi): el limiter se registra en la app y el 429 responde en español
app.state.limiter = rate_limit.limiter
app.add_exception_handler(RateLimitExceeded, rate_limit.rate_limit_exceeded_handler)

# Middlewares: el último que se agrega es el más externo. CORS va por fuera para que incluso las
# respuestas de error (401, 403, 429...) lleven las cabeceras CORS y el frontend pueda leerlas.
app.add_middleware(RequestMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # lista explícita de frontends autorizados, nunca "*" con credenciales
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Cabeceras propias que el JavaScript del frontend puede leer en la respuesta
    expose_headers=["X-Request-ID", "X-Process-Time", "X-App-Name", "X-API-Version"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(device_router)
app.include_router(loan_router)


def get_api_info() -> dict:
    """Configuración general y de seguridad de la API (sin valores secretos), disponible como dependencia."""
    return {
        "app_name": APP_NAME,
        "version": API_VERSION,
        "database": "SQLite",
        "auth": {"scheme": "OAuth2 Password + JWT Bearer", "algorithm": ALGORITHM,
                 "token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES},
        "cors_origins": CORS_ORIGINS,
        "rate_limiting": {
            "enabled": RATE_LIMIT_ENABLED,
            "POST /auth/login": rate_limit.LOGIN_LIMIT,
            "POST /auth/register": rate_limit.REGISTER_LIMIT,
            "GET /users": rate_limit.LIST_USERS_LIMIT,
            "POST /loans": rate_limit.CREATE_LOAN_LIMIT,
        },
    }


@app.get("/", tags=["Security"], summary="Endpoint raíz", description="Verifica que la API esté en funcionamiento.")
def root():
    return {"mensaje": "Bienvenido a device_systems API"}


@app.get(
    "/info",
    tags=["Security"],
    summary="Información y configuración de seguridad",
    description=(
        "Devuelve nombre, versión, esquema de autenticación, orígenes CORS autorizados y límites de peticiones. "
        "Nunca expone la SECRET_KEY."
    ),
    response_description="Configuración general y de seguridad de la API.",
)
def api_info(info: dict = Depends(get_api_info)):
    return info
