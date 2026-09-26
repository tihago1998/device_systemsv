from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

DeviceType = Literal["laptop", "tablet", "proyector", "camara", "router", "monitor"]

DEVICE_EXAMPLE = {
    "name": "Laptop Lenovo ThinkPad",
    "serial_number": "LEN-2024-001",
    "device_type": "laptop",
    "brand": "Lenovo",
    "is_available": True,
}


class DeviceBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Nombre descriptivo del equipo")
    serial_number: str = Field(..., min_length=3, max_length=50, description="Número de serie único del equipo")
    device_type: DeviceType = Field(..., description="Tipo: laptop, tablet, proyector, camara, router o monitor")
    brand: Optional[str] = Field(None, max_length=50, description="Marca del equipo (opcional)")


class DeviceCreate(DeviceBase):
    """Entrada para registrar un dispositivo (POST). is_available es opcional y por defecto es True."""
    is_available: bool = True

    model_config = ConfigDict(json_schema_extra={"examples": [DEVICE_EXAMPLE]})


class DeviceUpdate(DeviceBase):
    """Entrada para actualizar completamente un dispositivo (PUT): todos los campos son obligatorios."""
    is_available: bool

    model_config = ConfigDict(json_schema_extra={"examples": [{**DEVICE_EXAMPLE, "name": "Laptop Lenovo ThinkPad E14"}]})


class DevicePatch(BaseModel):
    """Entrada para actualizar parcialmente un dispositivo (PATCH): todos los campos son opcionales."""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    serial_number: Optional[str] = Field(None, min_length=3, max_length=50)
    device_type: Optional[DeviceType] = None
    brand: Optional[str] = Field(None, max_length=50)
    is_available: Optional[bool] = None

    model_config = ConfigDict(json_schema_extra={"examples": [{"brand": "Lenovo"}]})


class DeviceResponse(DeviceBase):
    """Salida: datos de un dispositivo guardado en la base de datos."""
    id: int
    is_available: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{"id": 1, **DEVICE_EXAMPLE, "created_at": "2026-09-26T10:00:00"}]},
    )
