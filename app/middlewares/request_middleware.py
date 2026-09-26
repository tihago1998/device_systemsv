import logging
import re
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import API_VERSION, APP_NAME

logger = logging.getLogger("device_systems.requests")

# Solo se propaga un X-Request-ID recibido si tiene un formato seguro (evita inyectar texto en los logs)
REQUEST_ID_VALIDO = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class RequestMiddleware(BaseHTTPMiddleware):
    """Middleware global: trazabilidad (X-Request-ID, log de cada petición), tiempo de respuesta y cabeceras."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", "")
        if not REQUEST_ID_VALIDO.match(request_id):
            request_id = uuid.uuid4().hex[:8]
        request.state.request_id = request_id

        inicio = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("%s %s -> 500 [request_id=%s]", request.method, request.url.path, request_id)
            raise
        duracion = time.perf_counter() - inicio

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duracion:.4f}"
        response.headers["X-App-Name"] = APP_NAME
        response.headers["X-API-Version"] = API_VERSION
        # Cabeceras de seguridad básicas: el navegador no adivina el tipo de contenido ni muestra la API en iframes
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"

        logger.info(
            "%s %s -> %s (%.4fs) [request_id=%s]",
            request.method, request.url.path, response.status_code, duracion, request_id,
        )
        return response
