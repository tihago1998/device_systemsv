from fastapi import Depends, FastAPI, Response

from app.dependencies.user_dependencies import get_api_info
from app.routes.device_routes import router as device_router
from app.routes.loan_routes import router as loan_router
from app.routes.user_routes import router as user_router

API_VERSION = "4.0.0"

# Las tablas ya no se crean aquí con create_all: la estructura de la base de datos
# se versiona con Alembic (alembic upgrade head).

tags_metadata = [
    {"name": "Users", "description": "Gestión de usuarios: CRUD, filtros, sus préstamos y sus dispositivos asignados."},
    {"name": "Devices", "description": "Equipos tecnológicos disponibles para préstamo: CRUD, filtros, búsqueda e historial."},
    {"name": "Loans", "description": "Préstamos de dispositivos a usuarios: registro, devolución y consultas con joins y filtros."},
    {"name": "Root", "description": "Estado e información general de la API."},
]

app = FastAPI(
    title="device_systems API",
    description=(
        "API REST para gestionar usuarios, dispositivos tecnológicos y préstamos del sistema device_systems. "
        "Persistencia con SQLAlchemy, migraciones con Alembic, relaciones entre modelos y consultas con joins."
    ),
    version=API_VERSION,
    contact={
        "name": "Santiago Varela Peña",
        "email": "santiago@example.com",
    },
    openapi_tags=tags_metadata,
)

app.include_router(user_router)
app.include_router(device_router)
app.include_router(loan_router)


@app.middleware("http")
async def agregar_cabeceras(request, call_next):
    response: Response = await call_next(request)
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = API_VERSION
    return response


@app.get("/", tags=["Root"], summary="Endpoint raíz", description="Verifica que la API esté en funcionamiento.")
def root():
    return {"mensaje": "Bienvenido a device_systems API"}


@app.get(
    "/info",
    tags=["Root"],
    summary="Información de la API",
    description="Devuelve la configuración general de la API, obtenida mediante la dependencia get_api_info.",
    response_description="Nombre, versión y base de datos de la API.",
)
def api_info(info: dict = Depends(get_api_info)):
    return info
