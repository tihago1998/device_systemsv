from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal, Optional

Role = Literal["admin", "support", "user"]


class UserBase(BaseModel):
    name: str = Field(..., min_length=3, description="Nombre completo del usuario")
    email: EmailStr
    role: Role
    is_active: bool = True


class UserCreate(UserBase):
    """Modelo de entrada para crear (POST) o reemplazar (PUT) un usuario."""
    pass


class UserResponse(UserBase):
    """Modelo de salida: estandariza y controla lo que se expone."""
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserPatch(BaseModel):
    """Modelo para PATCH: todos los campos son opcionales."""
    name: Optional[str] = Field(None, min_length=3)
    email: Optional[EmailStr] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None
