from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import get_password_hash, verify_password
from app.models.user_model import User
from app.schemas.auth_schema import UserLogin, UserRegister
from app.services import user_service

# Hash de referencia: si el correo no existe se verifica igual contra él, para que la respuesta tarde
# lo mismo y no se pueda averiguar qué correos están registrados midiendo el tiempo
_HASH_FICTICIO = get_password_hash("NoExiste123")


def register_user(db: Session, data: UserRegister, current_user: Optional[User] = None) -> User:
    """Registra un usuario. Solo un admin autenticado puede crear cuentas admin o support."""
    if data.role != "user" and (current_user is None or current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede registrar usuarios con rol admin o support",
        )
    user_data = data.model_dump(exclude={"confirm_password"})
    return user_service.create_user(db, {**user_data, "is_active": True})


def authenticate_user(db: Session, credentials: UserLogin) -> Optional[User]:
    """Devuelve el usuario si el correo y la contraseña son correctos; si no, None."""
    user = user_service.get_user_by_email(db, credentials.email)
    if user is None:
        verify_password(credentials.password, _HASH_FICTICIO)
        return None
    if not verify_password(credentials.password, user.hashed_password):
        return None
    return user
