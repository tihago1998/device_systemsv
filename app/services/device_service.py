from typing import Literal, Optional

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.device_model import Device
from app.models.loan_model import Loan

OrderField = Literal["id", "name", "created_at"]
OrderDirection = Literal["asc", "desc"]


def get_device_by_id(db: Session, device_id: int) -> Optional[Device]:
    return db.get(Device, device_id)


def get_device_by_serial(db: Session, serial_number: str) -> Optional[Device]:
    return db.scalars(select(Device).where(Device.serial_number == serial_number)).first()


def has_active_loan(db: Session, device_id: int) -> bool:
    stmt = select(Loan.id).where(and_(Loan.device_id == device_id, Loan.status.in_(["active", "overdue"])))
    return db.scalars(stmt).first() is not None


def _validar_serial_unico(db: Session, serial_number: str, excluir_id: Optional[int] = None) -> None:
    """Lanza 400 si el número de serie ya pertenece a otro dispositivo."""
    existing = get_device_by_serial(db, serial_number)
    if existing is not None and existing.id != excluir_id:
        raise HTTPException(status_code=400, detail="El número de serie ya está registrado")


def _validar_disponibilidad(db: Session, device: Device, fields: dict) -> None:
    """Regla de negocio: un equipo con préstamo activo no puede marcarse como disponible a mano (409)."""
    if fields.get("is_available") is True and not device.is_available and has_active_loan(db, device.id):
        raise HTTPException(
            status_code=409,
            detail="El dispositivo tiene un préstamo activo; se libera al registrar la devolución",
        )


def _guardar(db: Session, device: Device) -> Device:
    """Confirma los cambios; si la base de datos rechaza el serial por unique, responde 400."""
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="El número de serie ya está registrado")
    db.refresh(device)
    return device


def list_devices(
    db: Session,
    device_type: Optional[str] = None,
    is_available: Optional[bool] = None,
    brand: Optional[str] = None,
    search: Optional[str] = None,
    order_by: OrderField = "id",
    order: OrderDirection = "asc",
    skip: int = 0,
    limit: int = 100,
) -> list[Device]:
    stmt = select(Device)
    if device_type is not None:
        stmt = stmt.where(Device.device_type == device_type)
    if is_available is not None:
        stmt = stmt.where(Device.is_available == is_available)
    if brand:
        # Sin distinguir mayúsculas: brand=lenovo encuentra "Lenovo"
        stmt = stmt.where(func.lower(Device.brand) == brand.strip().lower())
    if search:
        patron = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(Device.name.ilike(patron), Device.serial_number.ilike(patron), Device.brand.ilike(patron))
        )
    column = getattr(Device, order_by)
    stmt = stmt.order_by(column.desc() if order == "desc" else column.asc())
    return list(db.scalars(stmt.offset(skip).limit(limit)))


def create_device(db: Session, device_data: dict) -> Device:
    _validar_serial_unico(db, device_data["serial_number"])
    device = Device(**device_data)
    db.add(device)
    return _guardar(db, device)


def update_device_full(db: Session, device: Device, device_data: dict) -> Device:
    """PUT: reemplaza todos los campos editables del dispositivo."""
    _validar_serial_unico(db, device_data["serial_number"], excluir_id=device.id)
    _validar_disponibilidad(db, device, device_data)
    for field, value in device_data.items():
        setattr(device, field, value)
    return _guardar(db, device)


def update_device_partial(db: Session, device: Device, fields: dict) -> Device:
    """PATCH: actualiza solo los campos enviados."""
    if not fields:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")
    if "serial_number" in fields:
        _validar_serial_unico(db, fields["serial_number"], excluir_id=device.id)
    _validar_disponibilidad(db, device, fields)
    for field, value in fields.items():
        setattr(device, field, value)
    return _guardar(db, device)


def delete_device(db: Session, device: Device) -> None:
    """Elimina un dispositivo; si tiene préstamos registrados se conserva el historial (409)."""
    if device.loans:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar un dispositivo con préstamos registrados (se conserva el historial)",
        )
    db.delete(device)
    db.commit()
