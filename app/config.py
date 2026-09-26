import os

from dotenv import load_dotenv

# Carga las variables del archivo .env (si existe) antes de leerlas
load_dotenv()


def _lista(valor: str) -> list[str]:
    return [item.strip() for item in valor.split(",") if item.strip()]


APP_NAME = "device_systems"
API_VERSION = "5.0.0"

# JWT: la clave secreta NUNCA se escribe en el código; se toma del .env
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# CORS: orígenes (frontends) autorizados a consumir la API
CORS_ORIGINS = _lista(os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"))

# Rate limiting: se puede desactivar solo para pruebas automatizadas
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

if not SECRET_KEY:
    raise RuntimeError("Falta SECRET_KEY: copie .env.example como .env y defina una clave secreta")
