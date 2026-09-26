from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["admin", "support", "user"]


class UserBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Nombre completo del usuario")
    email: EmailStr = Field(..., description="Correo electrónico único del usuario")
    role: Role = Field(..., description="Rol del usuario: admin, support o user")


class UserCreate(UserBase):
    """Entrada para crear un usuario (POST). is_active es opcional y por defecto es True."""
    is_active: bool = True


class UserUpdate(UserBase):
    """Entrada para actualizar completamente un usuario (PUT): todos los campos son obligatorios."""
    is_active: bool


class UserPatch(BaseModel):
    """Entrada para actualizar parcialmente un usuario (PATCH): todos los campos son opcionales."""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Salida: controla lo que la API expone de un usuario de la base de datos."""
    id: int
    is_active: bool
    created_at: datetime

    # Permite construir el schema directamente desde el objeto SQLAlchemy
    model_config = ConfigDict(from_attributes=True)
