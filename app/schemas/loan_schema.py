from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.device_schema import DeviceType

LoanStatus = Literal["active", "returned", "overdue"]


class LoanCreate(BaseModel):
    """Entrada para registrar un préstamo (POST): quién recibe el equipo y cuál equipo."""
    user_id: int = Field(..., gt=0, description="ID del usuario que recibe el equipo")
    device_id: int = Field(..., gt=0, description="ID del dispositivo que se presta")

    model_config = ConfigDict(json_schema_extra={"examples": [{"user_id": 1, "device_id": 1}]})


class LoanUpdate(BaseModel):
    """Entrada para cambiar el estado de un préstamo sin devolverlo (p. ej. marcarlo como vencido)."""
    status: Literal["active", "overdue"] = Field(..., description="Nuevo estado: active u overdue")

    model_config = ConfigDict(json_schema_extra={"examples": [{"status": "overdue"}]})


class LoanResponse(BaseModel):
    """Salida básica de un préstamo (solo los IDs relacionados)."""
    id: int
    user_id: int
    device_id: int
    loan_date: datetime
    return_date: Optional[datetime] = None
    status: LoanStatus

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{
            "id": 1, "user_id": 1, "device_id": 1, "loan_date": "2026-09-26T10:00:00",
            "return_date": None, "status": "active",
        }]},
    )


class UserBasic(BaseModel):
    """Datos básicos del usuario dentro de un préstamo."""
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class DeviceBasic(BaseModel):
    """Datos básicos del dispositivo dentro de un préstamo."""
    id: int
    name: str
    serial_number: str
    device_type: DeviceType

    model_config = ConfigDict(from_attributes=True)


class LoanDetailResponse(BaseModel):
    """Salida con información relacionada: préstamo + usuario + dispositivo (resultado de un join)."""
    loan_id: int = Field(..., validation_alias="id")
    status: LoanStatus
    loan_date: datetime
    return_date: Optional[datetime] = None
    user: UserBasic
    device: DeviceBasic

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{
            "loan_id": 1,
            "status": "active",
            "loan_date": "2026-09-26T10:00:00",
            "return_date": None,
            "user": {"id": 1, "name": "Ana Pérez", "email": "ana@sena.edu.co"},
            "device": {"id": 3, "name": "Laptop Lenovo ThinkPad", "serial_number": "LEN-2024-001", "device_type": "laptop"},
        }]},
    )
