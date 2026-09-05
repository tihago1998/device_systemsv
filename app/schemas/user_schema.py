from pydantic import BaseModel, EmailStr, Field
from typing import Literal


class UserBase(BaseModel):
    name: str = Field(..., min_length=3, description="Nombre completo del usuario")
    email: EmailStr
    role: Literal["admin", "support", "user"]
    is_active: bool = True


class UserCreate(UserBase):
    """Modelo de entrada para crear un usuario (POST /users)."""
    pass


class UserResponse(UserBase):
    """Modelo de salida: estandariza y controla lo que se expone."""
    id: int

    class Config:
        from_attributes = True

from typing import Optional


class UserUpdate(BaseModel):
    """Modelo para PUT: todos los campos son requeridos (igual que UserCreate)."""
    pass  # UserCreate ya sirve para esto, no hace falta duplicar


class UserPatch(BaseModel):
    """Modelo para PATCH: todos los campos son opcionales."""
    name: Optional[str] = Field(None, min_length=3)
    email: Optional[EmailStr] = None
    role: Optional[Literal["admin", "support", "user"]] = None
    is_active: Optional[bool] = None        