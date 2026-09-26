import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Role = Literal["admin", "support", "user"]

USER_EXAMPLE = {"name": "Ana Pérez", "email": "ana@sena.edu.co", "role": "user", "is_active": True}

# bcrypt solo usa los primeros 72 bytes de la contraseña: por eso se limita la longitud máxima
PASSWORD_FIELD = Field(
    ...,
    min_length=8,
    max_length=72,
    description="Mínimo 8 caracteres, con al menos una mayúscula, una minúscula y un número, sin espacios",
)


def validar_password_segura(password: str) -> str:
    """Reglas de contraseña segura, compartidas por el registro (/auth/register) y POST /users."""
    errores = []
    if not re.search(r"[A-Z]", password):
        errores.append("al menos una letra mayúscula")
    if not re.search(r"[a-z]", password):
        errores.append("al menos una letra minúscula")
    if not re.search(r"\d", password):
        errores.append("al menos un número")
    if re.search(r"\s", password):
        errores.append("no contener espacios en blanco")
    if errores:
        raise ValueError("La contraseña debe tener: " + ", ".join(errores))
    return password


def normalizar_nombre(name: str) -> str:
    """Quita espacios sobrantes y rechaza nombres formados solo por espacios."""
    name = " ".join(name.split())
    if len(name) < 3:
        raise ValueError("El nombre debe tener al menos 3 caracteres (sin contar espacios)")
    return name


class UserBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Nombre completo del usuario")
    email: EmailStr = Field(..., description="Correo electrónico único del usuario")
    role: Role = Field(..., description="Rol del usuario: admin, support o user")

    @field_validator("name")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        return normalizar_nombre(value)

    @field_validator("email")
    @classmethod
    def email_minusculas(cls, value: str) -> str:
        # Ana@Sena.edu.co y ana@sena.edu.co son el mismo correo: se guarda siempre en minúsculas
        return value.lower()


class UserCreate(UserBase):
    """Entrada para crear un usuario (POST, solo admin). La contraseña se guarda como hash bcrypt."""
    password: str = PASSWORD_FIELD
    is_active: bool = True

    @field_validator("password")
    @classmethod
    def validar_password(cls, value: str) -> str:
        return validar_password_segura(value)

    model_config = ConfigDict(json_schema_extra={"examples": [{**USER_EXAMPLE, "password": "Segura2026"}]})


class UserUpdate(UserBase):
    """Entrada para actualizar completamente un usuario (PUT): todos los campos son obligatorios."""
    is_active: bool

    model_config = ConfigDict(json_schema_extra={"examples": [{**USER_EXAMPLE, "role": "support"}]})


class UserPatch(BaseModel):
    """Entrada para actualizar parcialmente un usuario (PATCH): todos los campos son opcionales."""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validar_nombre(cls, value: Optional[str]) -> Optional[str]:
        return normalizar_nombre(value) if value is not None else value

    @field_validator("email")
    @classmethod
    def email_minusculas(cls, value: Optional[str]) -> Optional[str]:
        return value.lower() if value is not None else value

    model_config = ConfigDict(json_schema_extra={"examples": [{"role": "support"}]})


class UserResponse(UserBase):
    """Salida: controla lo que la API expone de un usuario. hashed_password nunca se incluye."""
    id: int
    is_active: bool
    created_at: datetime

    # Permite construir el schema directamente desde el objeto SQLAlchemy
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{"id": 1, **USER_EXAMPLE, "created_at": "2026-09-26T10:00:00"}]},
    )
