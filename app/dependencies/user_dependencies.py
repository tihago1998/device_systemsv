from typing import Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.models.user_model import User
from app.services import user_service

ROLES_PERMITIDOS = {"admin", "support", "user"}


def get_user_or_404(user_id: int, db: Session = Depends(get_db)) -> User:
    """Dependencia reutilizable: obtiene un usuario de la base de datos o lanza 404."""
    user = user_service.get_user_by_id(db, user_id)
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
