from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.models.device_model import Device
from app.services import device_service


def get_device_or_404(device_id: int, db: Session = Depends(get_db)) -> Device:
    """Dependencia reutilizable: obtiene un dispositivo de la base de datos o lanza 404."""
    device = device_service.get_device_by_id(db, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return device
