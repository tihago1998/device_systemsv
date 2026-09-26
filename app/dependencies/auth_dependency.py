from typing import Callable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.dependencies.database_dependency import get_db
from app.models.user_model import User
from app.schemas.auth_schema import TokenData
from app.services import user_service

# Le indica a FastAPI (y a Swagger) que el token se obtiene en POST /auth/login y se envía en
# la cabecera Authorization: Bearer <token>. Si falta la cabecera responde 401 automáticamente.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
# Variante que no exige token: se usa donde la autenticación es opcional (registro)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# Respuestas de error para documentar en Swagger las rutas protegidas
AUTH_ERRORS = {401: {"description": "Token ausente, inválido o vencido"}}
ROLE_ERRORS = {**AUTH_ERRORS, 403: {"description": "El usuario no tiene permisos para esta operación"}}


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token de acceso",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Valida el JWT (firma y vencimiento) y devuelve el usuario dueño del token (401 si no es válido)."""
    payload = decode_access_token(token)
    if payload is None:
        raise _credentials_exception()
    try:
        token_data = TokenData(email=payload.get("sub"), role=payload.get("role"))
    except ValidationError:
        raise _credentials_exception()
    if token_data.email is None:
        raise _credentials_exception()
    user = user_service.get_user_by_email(db, token_data.email)
    if user is None:
        raise _credentials_exception()
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Igual que get_current_user, pero rechaza usuarios desactivados (403)."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")
    return current_user


def require_roles(*roles: str) -> Callable[..., User]:
    """Crea una dependencia que solo deja pasar a usuarios activos con alguno de los roles indicados (403)."""

    def verificar_rol(current_user: User = Depends(get_current_active_user)) -> User:
        # El rol se toma de la base de datos y no del token: si un admin cambia el rol, aplica de inmediato
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso denegado: se requiere rol {' o '.join(roles)}",
            )
        return current_user

    return verificar_rol


require_admin = require_roles("admin")
require_admin_or_support = require_roles("admin", "support")


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)
) -> Optional[User]:
    """Devuelve el usuario si se envió un token; None si no se envió. Un token inválido sigue siendo 401."""
    if token is None:
        return None
    return get_current_active_user(get_current_user(token, db))


def verificar_propietario_o_staff(current_user: User, user_id: int) -> None:
    """Un usuario con rol user solo puede ver u operar sus propios préstamos; admin y support, todos."""
    if current_user.role == "user" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado: solo puede acceder a sus propios préstamos",
        )
