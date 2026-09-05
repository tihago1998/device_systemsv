from fastapi import APIRouter, HTTPException, Query, Path, Response
from typing import List, Optional
from app.schemas.user_schema import UserCreate, UserResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


def set_headers(response: Response):
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "1.0"


@router.get("/", response_model=List[UserResponse])
def list_users(
    response: Response,
    role: Optional[str] = Query(None, description="Filtrar por rol: admin, support, user"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
):
    set_headers(response)
    return user_service.list_users(role, is_active)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    response: Response,
    user_id: int = Path(..., gt=0, description="ID del usuario a consultar"),
):
    set_headers(response)
    return user_service.get_user_by_id(user_id)


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, response: Response):
    set_headers(response)
    return user_service.create_user(user.model_dump())

from app.schemas.user_schema import UserCreate, UserResponse, UserPatch


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserCreate, response: Response):
    set_headers(response)
    return user_service.update_user_full(user_id, user.model_dump())


@router.patch("/{user_id}", response_model=UserResponse)
def patch_user(user_id: int, user: UserPatch, response: Response):
    set_headers(response)
    fields = user.model_dump(exclude_unset=True)
    return user_service.update_user_partial(user_id, fields)    