from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.dependencies.user_dependencies import get_user_or_404, validar_rol
from app.models.user_model import User
from app.schemas.user_schema import UserCreate, UserPatch, UserResponse, UserUpdate
from app.services import user_service

# Las cabeceras X-App-Name y X-API-Version las agrega el middleware de app/main.py
router = APIRouter(prefix="/users", tags=["Users"])

ERROR_404 = {404: {"description": "Usuario no encontrado"}}
ERROR_400_EMAIL = {400: {"description": "El correo ya está registrado"}}


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Listar usuarios",
    description=(
        "Lista los usuarios guardados en la base de datos. Permite filtrar por rol y estado, "
        "ordenar por id, nombre o fecha de creación, y paginar con skip y limit."
    ),
    response_description="Lista de usuarios que cumplen los filtros aplicados.",
    responses={400: {"description": "Rol no permitido"}},
)
def list_users(
    role: Optional[str] = Depends(validar_rol),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    order_by: Literal["id", "name", "created_at"] = Query("id", description="Campo por el que se ordena"),
    order: Literal["asc", "desc"] = Query("asc", description="Dirección del orden"),
    skip: int = Query(0, ge=0, description="Cantidad de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Cantidad máxima de registros a devolver"),
    db: Session = Depends(get_db),
):
    return user_service.list_users(db, role, is_active, order_by, order, skip, limit)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Consultar usuario por ID",
    description="Obtiene los datos de un usuario específico a partir de su ID.",
    response_description="Datos del usuario solicitado.",
    responses=ERROR_404,
)
def get_user(user: User = Depends(get_user_or_404)):
    return user


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    description="Registra un nuevo usuario en la base de datos, validando que el correo no esté duplicado.",
    response_description="Usuario creado con su ID y fecha de creación.",
    responses=ERROR_400_EMAIL,
)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, user.model_dump())


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario (completo)",
    description="Reemplaza todos los datos de un usuario existente. Requiere name, email, role e is_active.",
    response_description="Usuario con los datos actualizados.",
    responses={**ERROR_404, **ERROR_400_EMAIL},
)
def update_user(
    user: UserUpdate,
    current_user: User = Depends(get_user_or_404),
    db: Session = Depends(get_db),
):
    return user_service.update_user_full(db, current_user, user.model_dump())


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario (parcial)",
    description="Actualiza solo los campos enviados de un usuario existente. Si no se envía ningún campo responde 400.",
    response_description="Usuario con los campos actualizados.",
    responses={**ERROR_404, 400: {"description": "Correo duplicado o no se enviaron campos"}},
)
def patch_user(
    user: UserPatch,
    current_user: User = Depends(get_user_or_404),
    db: Session = Depends(get_db),
):
    # exclude_none evita guardar valores null (p. ej. {"name": null}) en columnas obligatorias
    fields = user.model_dump(exclude_unset=True, exclude_none=True)
    return user_service.update_user_partial(db, current_user, fields)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar usuario",
    description="Elimina un usuario existente de la base de datos.",
    response_description="Usuario eliminado exitosamente (sin contenido de respuesta).",
    responses=ERROR_404,
)
def remove_user(user: User = Depends(get_user_or_404), db: Session = Depends(get_db)):
    user_service.delete_user(db, user)
    return None
