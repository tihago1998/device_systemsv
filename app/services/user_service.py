from typing import Literal, Optional

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user_model import User

OrderField = Literal["id", "name", "created_at"]
OrderDirection = Literal["asc", "desc"]


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def _validar_email_unico(db: Session, email: str, excluir_id: Optional[int] = None) -> None:
    """Lanza 400 si el correo ya pertenece a otro usuario."""
    existing = get_user_by_email(db, email)
    if existing is not None and existing.id != excluir_id:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")


def _guardar(db: Session, user: User) -> User:
    """Confirma los cambios; si la base de datos rechaza el email por unique, responde 400."""
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    db.refresh(user)
    return user


def filter_by_role(query, role: str):
    return query.filter(User.role == role)


def filter_by_status(query, is_active: bool):
    return query.filter(User.is_active == is_active)


def order_users(query, order_by: OrderField = "id", order: OrderDirection = "asc"):
    column = getattr(User, order_by)
    return query.order_by(column.desc() if order == "desc" else column.asc())


def list_users(
    db: Session,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    order_by: OrderField = "id",
    order: OrderDirection = "asc",
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
) -> list[User]:
    query = db.query(User)
    if role is not None:
        query = filter_by_role(query, role)
    if is_active is not None:
        query = filter_by_status(query, is_active)
    if search:
        patron = f"%{search.strip()}%"
        query = query.filter(or_(User.name.ilike(patron), User.email.ilike(patron)))
    query = order_users(query, order_by, order)
    return query.offset(skip).limit(limit).all()


def create_user(db: Session, user_data: dict) -> User:
    _validar_email_unico(db, user_data["email"])
    user = User(**user_data)
    db.add(user)
    return _guardar(db, user)


def update_user_full(db: Session, user: User, user_data: dict) -> User:
    """PUT: reemplaza todos los campos editables del usuario."""
    _validar_email_unico(db, user_data["email"], excluir_id=user.id)
    for field, value in user_data.items():
        setattr(user, field, value)
    return _guardar(db, user)


def update_user_partial(db: Session, user: User, fields: dict) -> User:
    """PATCH: actualiza solo los campos enviados."""
    if not fields:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")
    if "email" in fields:
        _validar_email_unico(db, fields["email"], excluir_id=user.id)
    for field, value in fields.items():
        setattr(user, field, value)
    return _guardar(db, user)


def delete_user(db: Session, user: User) -> None:
    """Elimina un usuario; si tiene préstamos registrados se conserva el historial (409)."""
    if user.loans:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar un usuario con préstamos registrados (se conserva el historial)",
        )
    db.delete(user)
    db.commit()
