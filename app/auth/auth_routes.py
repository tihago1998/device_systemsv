from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.auth.security import create_access_token
from app.dependencies.auth_dependency import AUTH_ERRORS, get_current_active_user, get_optional_user
from app.dependencies.database_dependency import get_db
from app.middlewares.rate_limit import LOGIN_LIMIT, RATE_LIMIT_ERROR, REGISTER_LIMIT, limiter
from app.models.user_model import User
from app.schemas.auth_schema import Token, UserLogin, UserRegister
from app.schemas.user_schema import UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario",
    description=(
        "Crea un usuario con contraseña segura (mínimo 8 caracteres, mayúscula, minúscula, número y sin espacios). "
        "La contraseña se guarda como hash bcrypt. Cualquier persona puede registrarse con rol user; "
        "para registrar admin o support se debe enviar el token de un admin. Límite: 3 solicitudes por minuto."
    ),
    response_description="Usuario registrado (sin la contraseña ni su hash).",
    responses={
        400: {"description": "El correo ya está registrado"},
        401: {"description": "Se envió un token inválido o vencido"},
        403: {"description": "Solo un admin puede registrar usuarios admin o support"},
        422: {"description": "Datos inválidos: contraseña débil, email mal escrito, rol no permitido, etc."},
        **RATE_LIMIT_ERROR,
    },
)
@limiter.limit(REGISTER_LIMIT)
def register(
    request: Request,
    data: UserRegister,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    return auth_service.register_user(db, data, current_user)


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión (OAuth2)",
    description=(
        "Recibe un formulario OAuth2 (username = correo, password) y, si las credenciales son correctas, "
        "devuelve un token JWT que vence según ACCESS_TOKEN_EXPIRE_MINUTES. Límite: 5 solicitudes por minuto."
    ),
    response_description="Token de acceso JWT.",
    responses={
        401: {"description": "Correo o contraseña incorrectos"},
        403: {"description": "Usuario inactivo"},
        **RATE_LIMIT_ERROR,
    },
)
@limiter.limit(LOGIN_LIMIT)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Correo o contraseña incorrectos",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        credentials = UserLogin(email=form_data.username, password=form_data.password)
    except ValidationError:
        raise credenciales_invalidas

    user = auth_service.authenticate_user(db, credentials)
    if user is None:
        raise credenciales_invalidas
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    access_token = create_access_token({"sub": user.email, "role": user.role})
    return Token(access_token=access_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Usuario autenticado",
    description="Devuelve los datos del usuario dueño del token enviado en Authorization: Bearer <token>.",
    response_description="Datos del usuario autenticado (sin hashed_password).",
    responses={**AUTH_ERRORS, 403: {"description": "Usuario inactivo"}},
)
def read_me(current_user: User = Depends(get_current_active_user)):
    return current_user
