from fastapi import APIRouter, HTTPException, Query, Path, Response, Depends, status
from typing import List, Optional
from app.schemas.user_schema import UserCreate, UserResponse, UserPatch
from app.services import user_service
from app.dependencies.user_dependencies import get_user_or_404

router = APIRouter(prefix="/users", tags=["Users"])


def set_headers(response: Response):
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "2.0.0"


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Listar usuarios",
    description="Lista todos los usuarios registrados, con filtros opcionales por rol y estado activo.",
    response_description="Lista de usuarios que cumplen los filtros aplicados.",
)
def list_users(
    response: Response,
    role: Optional[str] = Query(None, description="Filtrar por rol: admin, support, user"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
):
    set_headers(response)
    return user_service.list_users(role, is_active)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Consultar usuario por ID",
    description="Obtiene los datos de un usuario específico a partir de su ID.",
    response_description="Datos del usuario solicitado.",
)
def get_user(response: Response, user: dict = Depends(get_user_or_404)):
    set_headers(response)
    return user


@router.post(
    "/",
    response_model=UserResponse,
    status_code=201,
    summary="Crear usuario",
    description="Registra un nuevo usuario en el sistema, validando que el correo no esté duplicado.",
    response_description="Usuario creado con su ID asignado.",
)
def create_user(user: UserCreate, response: Response):
    set_headers(response)
    return user_service.create_user(user.model_dump())


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario (completo)",
    description="Reemplaza todos los datos de un usuario existente.",
    response_description="Usuario con los datos actualizados.",
)
def update_user(user_id: int, user: UserCreate, response: Response):
    set_headers(response)
    return user_service.update_user_full(user_id, user.model_dump())


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario (parcial)",
    description="Actualiza solo los campos enviados de un usuario existente.",
    response_description="Usuario con los campos actualizados.",
)
def patch_user(user_id: int, user: UserPatch, response: Response):
    set_headers(response)
    fields = user.model_dump(exclude_unset=True)
    return user_service.update_user_partial(user_id, fields)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar usuario",
    description="Elimina un usuario existente del sistema.",
    response_description="Usuario eliminado exitosamente (sin contenido de respuesta).",
)
def remove_user(user_id: int, response: Response):
    set_headers(response)
    user_service.delete_user(user_id)
    return None