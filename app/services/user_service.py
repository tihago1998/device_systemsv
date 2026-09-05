from fastapi import HTTPException
from app.data.users_db import fake_db, get_next_id


def list_users(role: str | None = None, is_active: bool | None = None) -> list[dict]:
    result = fake_db
    if role is not None:
        result = [u for u in result if u["role"] == role]
    if is_active is not None:
        result = [u for u in result if u["is_active"] == is_active]
    return result


def get_user_by_id(user_id: int) -> dict:
    user = next((u for u in fake_db if u["id"] == user_id), None)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


def create_user(user_data: dict) -> dict:
    if any(u["email"] == user_data["email"] for u in fake_db):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    new_user = dict(user_data)
    new_user["id"] = get_next_id()
    fake_db.append(new_user)
    return new_user