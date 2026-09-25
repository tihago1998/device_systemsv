from typing import Optional

from fastapi import HTTPException, Header, Query
from app.data.users_db import fake_db

ROLES_PERMITIDOS = {"admin", "support", "user"}


def get_user_or_404(user_id: int) -> dict:
    """Dependencia reutilizable: obtiene un usuario o lanza 404."""
    user = next((u for u in fake_db if u["id"] == user_id), None)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


def validar_rol(
    role: Optional[str] = Query(None, description="Filtrar por rol: admin, support, user"),
) -> Optional[str]:
    """Valida que el rol recibido como filtro sea uno de los permitidos (400 si no lo es)."""
    if role is not None and role not in ROLES_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Rol no permitido. Debe ser uno de: {', '.join(sorted(ROLES_PERMITIDOS))}"
        )
    return role


def get_api_info() -> dict:
    """Configuración general de la API, disponible como dependencia."""
    return {"app_name": "device_systems", "version": "2.0.0"}


def verificar_autenticacion(x_token: str = Header(None)) -> bool:
    """Simula autenticación básica mediante una cabecera personalizada."""
    if x_token != "secreto123":
        raise HTTPException(status_code=401, detail="Token de autenticación inválido o ausente")
    return True
