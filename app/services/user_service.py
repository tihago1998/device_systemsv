from fastapi import HTTPException
from app.data.users_db import fake_db, get_next_id


def _validar_email_unico(email: str, excluir_id: int | None = None) -> None:
    """Lanza 400 si el correo ya pertenece a otro usuario."""
    if any(u["email"] == email and u["id"] != excluir_id for u in fake_db):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")


def list_users(role: str | None = None, is_active: bool | None = None) -> list[dict]:
    result = fake_db
    if role is not None:
        result = [u for u in result if u["role"] == role]
    if is_active is not None:
        result = [u for u in result if u["is_active"] == is_active]
    return result


def create_user(user_data: dict) -> dict:
    _validar_email_unico(user_data["email"])
    new_user = dict(user_data)
    new_user["id"] = get_next_id()
    fake_db.append(new_user)
    return new_user


def update_user_full(user: dict, user_data: dict) -> dict:
    """PUT: reemplaza completamente los datos del usuario."""
    _validar_email_unico(user_data["email"], excluir_id=user["id"])
    user.update(user_data)
    return user


def update_user_partial(user: dict, fields: dict) -> dict:
    """PATCH: actualiza solo los campos enviados."""
    if not fields:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")
    if "email" in fields:
        _validar_email_unico(fields["email"], excluir_id=user["id"])
    user.update(fields)
    return user


def delete_user(user: dict) -> None:
    """Elimina un usuario existente."""
    fake_db.remove(user)
