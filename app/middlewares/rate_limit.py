from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import RATE_LIMIT_ENABLED

# Límites por endpoint (formato de slowapi: "cantidad/periodo")
LOGIN_LIMIT = "5/minute"
REGISTER_LIMIT = "3/minute"
LIST_USERS_LIMIT = "30/minute"
CREATE_LOAN_LIMIT = "10/minute"

# Cada cliente se identifica por su dirección IP; los contadores se guardan en memoria
limiter = Limiter(key_func=get_remote_address, enabled=RATE_LIMIT_ENABLED)

RATE_LIMIT_ERROR = {429: {"description": "Demasiadas solicitudes: se superó el límite de peticiones por minuto"}}


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Respuesta 429 en español cuando un cliente supera el límite de peticiones."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": f"Demasiadas solicitudes. Límite permitido: {exc.detail}. Intente de nuevo más tarde."},
        headers={"Retry-After": "60"},
    )
