from fastapi import FastAPI, Response
from app.routes.user_routes import router as user_router

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