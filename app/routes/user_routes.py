from fastapi import APIRouter, Query, Depends, status
from typing import List, Optional
from app.schemas.user_schema import UserCreate, UserResponse, UserPatch
from app.services import user_service
from app.dependencies.user_dependencies import get_user_or_404, validar_rol

# Las cabeceras X-App-Name y X-API-Version las agrega el middleware de app/main.py
router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Listar usuarios",
    description="Lista todos los usuarios registrados, con filtros opcionales por rol y estado activo.",
    response_description="Lista de usuarios que cumplen los filtros aplicados.",
)
def list_users(
    role: Optional[str] = Depends(validar_rol),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
):
    return user_service.list_users(role, is_active)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Consultar usuario por ID",
    description="Obtiene los datos de un usuario específico a partir de su ID.",
    response_description="Datos del usuario solicitado.",
)
def get_user(user: dict = Depends(get_user_or_404)):
    return user


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    description="Registra un nuevo usuario en el sistema, validando que el correo no esté duplicado.",
    response_description="Usuario creado con su ID asignado.",
)
def create_user(user: UserCreate):
    return user_service.create_user(user.model_dump())


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario (completo)",
    description="Reemplaza todos los datos de un usuario existente. Requiere name, email, role e is_active.",
    response_description="Usuario con los datos actualizados.",
)
def update_user(user: UserCreate, current_user: dict = Depends(get_user_or_404)):
    return user_service.update_user_full(current_user, user.model_dump())


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario (parcial)",
    description="Actualiza solo los campos enviados de un usuario existente. Si no se envía ningún campo responde 400.",
    response_description="Usuario con los campos actualizados.",
)
def patch_user(user: UserPatch, current_user: dict = Depends(get_user_or_404)):
    # exclude_none evita guardar valores null (p. ej. {"name": null}) que romperían el usuario
    fields = user.model_dump(exclude_unset=True, exclude_none=True)
    return user_service.update_user_partial(current_user, fields)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar usuario",
    description="Elimina un usuario existente del sistema.",
    response_description="Usuario eliminado exitosamente (sin contenido de respuesta).",
)
def remove_user(user: dict = Depends(get_user_or_404)):
    user_service.delete_user(user)
    return None
