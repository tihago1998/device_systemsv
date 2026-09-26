from datetime import date, datetime, time, timedelta
from typing import Literal, Optional

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, contains_eager

from app.models.device_model import Device
from app.models.loan_model import Loan
from app.models.user_model import User, utc_now

OrderDirection = Literal["asc", "desc"]


def get_loan_by_id(db: Session, loan_id: int) -> Optional[Loan]:
    return db.get(Loan, loan_id)


def list_loans(
    db: Session,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    device_id: Optional[int] = None,
    user_email: Optional[str] = None,
    device_type: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    order: OrderDirection = "desc",
    skip: int = 0,
    limit: int = 100,
) -> list[Loan]:
    """Consulta préstamos uniendo (join) las tablas users y devices para filtrar y devolver sus datos."""
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="Filtro inválido: date_from no puede ser mayor que date_to")

    condiciones = []
    if status is not None:
        condiciones.append(Loan.status == status)
    if user_id is not None:
        condiciones.append(Loan.user_id == user_id)
    if device_id is not None:
        condiciones.append(Loan.device_id == device_id)
    if user_email:
        condiciones.append(func.lower(User.email) == user_email.strip().lower())
    if device_type is not None:
        condiciones.append(Device.device_type == device_type)
    if date_from is not None:
        condiciones.append(Loan.loan_date >= datetime.combine(date_from, time.min))
    if date_to is not None:
        # Incluye todo el día date_to
        condiciones.append(Loan.loan_date < datetime.combine(date_to + timedelta(days=1), time.min))
    if search:
        patron = f"%{search.strip()}%"
        condiciones.append(or_(
            User.name.ilike(patron),
            User.email.ilike(patron),
            Device.name.ilike(patron),
            Device.serial_number.ilike(patron),
        ))

    stmt = (
        select(Loan)
        .join(Loan.user)
        .join(Loan.device)
        # contains_eager: reutiliza el join para cargar user y device sin consultas extra
        .options(contains_eager(Loan.user), contains_eager(Loan.device))
        .where(and_(*condiciones))
        .order_by(Loan.loan_date.desc() if order == "desc" else Loan.loan_date.asc(), Loan.id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).unique())


def list_devices_of_user(db: Session, user_id: int, only_active: bool = True) -> list[Device]:
    """Dispositivos que tiene (o tuvo) un usuario, usando un join entre devices y loans."""
    stmt = select(Device).join(Device.loans).where(Loan.user_id == user_id)
    if only_active:
        stmt = stmt.where(Loan.status.in_(["active", "overdue"]))
    return list(db.scalars(stmt.distinct().order_by(Device.id)))


def create_loan(db: Session, user_id: int, device_id: int) -> Loan:
    """Registra un préstamo validando usuario, dispositivo y disponibilidad; el equipo queda no disponible."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not user.is_active:
        raise HTTPException(status_code=409, detail="El usuario está inactivo y no puede recibir préstamos")
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    if not device.is_available:
        raise HTTPException(status_code=409, detail="El dispositivo no está disponible para préstamo")

    loan = Loan(user_id=user.id, device_id=device.id, status="active")
    device.is_available = False
    db.add(loan)
    db.commit()  # préstamo y cambio de disponibilidad se guardan juntos
    db.refresh(loan)
    return loan


def return_loan(db: Session, loan: Loan) -> Loan:
    """Registra la devolución: estado returned, fecha de devolución y el equipo vuelve a estar disponible."""
    if loan.status == "returned":
        raise HTTPException(status_code=409, detail="El préstamo ya fue devuelto")
    loan.status = "returned"
    loan.return_date = utc_now()
    loan.device.is_available = True
    db.commit()
    db.refresh(loan)
    return loan


def update_loan_status(db: Session, loan: Loan, status: str) -> Loan:
    """Cambia el estado de un préstamo abierto (active <-> overdue)."""
    if loan.status == "returned":
        raise HTTPException(status_code=409, detail="No se puede cambiar el estado de un préstamo ya devuelto")
    loan.status = status
    db.commit()
    db.refresh(loan)
    return loan
