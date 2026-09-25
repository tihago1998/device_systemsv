from fastapi import Depends, FastAPI, Response
from app.routes.user_routes import router as user_router
from app.dependencies.user_dependencies import get_api_info

app = FastAPI(
    title="device_systems API",
    description="API REST para la gestión de usuarios del sistema device_systems",
    version="2.0.0",
    contact={
        "name": "Santiago Varela Peña",
        "email": "santiago@example.com",
    },
)

app.include_router(user_router)


@app.middleware("http")
async def agregar_cabeceras(request, call_next):
    response: Response = await call_next(request)
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "2.0.0"
    return response


@app.get("/", tags=["Root"], summary="Endpoint raíz", description="Verifica que la API esté en funcionamiento.")
def root():
    return {"mensaje": "Bienvenido a device_systems API"}


@app.get(
    "/info",
    tags=["Root"],
    summary="Información de la API",
    description="Devuelve la configuración general de la API, obtenida mediante la dependencia get_api_info.",
    response_description="Nombre y versión de la API.",
)
def api_info(info: dict = Depends(get_api_info)):
    return info