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