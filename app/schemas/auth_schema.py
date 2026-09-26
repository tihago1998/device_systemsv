from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.schemas.user_schema import PASSWORD_FIELD, Role, normalizar_nombre, validar_password_segura


class UserRegister(BaseModel):
    """Entrada de POST /auth/register. La contraseña llega en texto plano solo aquí y se guarda como hash."""
    name: str = Field(..., min_length=3, max_length=100, description="Nombre completo del usuario")
    email: EmailStr = Field(..., description="Correo electrónico único; se usa como usuario para el login")
    password: str = PASSWORD_FIELD
    confirm_password: str = Field(..., description="Debe ser igual a password")
    role: Role = Field("user", description="Rol: user (por defecto). admin y support solo los puede asignar un admin")

    @field_validator("name")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        return normalizar_nombre(value)

    @field_validator("email")
    @classmethod
    def email_minusculas(cls, value: str) -> str:
        return value.lower()

    @field_validator("password")
    @classmethod
    def validar_password(cls, value: str) -> str:
        return validar_password_segura(value)

    @model_validator(mode="after")
    def validar_reglas_entre_campos(self) -> "UserRegister":
        # Reglas que dependen de más de un campo: solo se pueden validar con el modelo completo
        if self.password != self.confirm_password:
            raise ValueError("password y confirm_password no coinciden")
        usuario_correo = self.email.split("@")[0]
        if len(usuario_correo) >= 3 and usuario_correo in self.password.lower():
            raise ValueError("La contraseña no debe contener el usuario del correo electrónico")
        return self

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "name": "Ana Pérez",
        "email": "ana@sena.edu.co",
        "password": "Segura2026",
        "confirm_password": "Segura2026",
        "role": "user",
    }]})


class UserLogin(BaseModel):
    """Credenciales del login. En Swagger se envían como formulario OAuth2 (username = email)."""
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def email_minusculas(cls, value: str) -> str:
        return value.lower()


class Token(BaseModel):
    """Respuesta de POST /auth/login."""
    access_token: str = Field(..., description="JWT firmado que se envía en Authorization: Bearer <token>")
    token_type: Literal["bearer"] = "bearer"

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
    }]})


class TokenData(BaseModel):
    """Contenido (payload) que se extrae del JWT al validarlo."""
    email: Optional[EmailStr] = None
    role: Optional[Role] = None
