from fastapi import APIRouter, HTTPException, Query, Path, Response
from typing import List, Optional
from app.schemas.user_schema import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

fake_db: List[dict] = [
    {"id": 1, "name": "Ana Torres", "email": "ana@device.com", "role": "admin", "is_active": True},
    {"id": 2, "name": "Luis Pérez", "email": "luis@device.com", "role": "user", "is_active": False},
]


def get_next_id() -> int:
    return max((u["id"] for u in fake_db), default=0) + 1


@router.get("/", response_model=List[UserResponse])
def list_users(
    response: Response,
    role: Optional[str] = Query(None, description="Filtrar por rol: admin, support, user"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
):
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "1.0"

    result = fake_db
    if role is not None:
        result = [u for u in result if u["role"] == role]
    if is_active is not None:
        result = [u for u in result if u["is_active"] == is_active]
    return result


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    response: Response,
    user_id: int = Path(..., gt=0, description="ID del usuario a consultar"),
):
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "1.0"

    user = next((u for u in fake_db if u["id"] == user_id), None)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, response: Response):
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "1.0"

    if any(u["email"] == user.email for u in fake_db):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    new_user = user.model_dump()
    new_user["id"] = get_next_id()
    fake_db.append(new_user)
    return new_user