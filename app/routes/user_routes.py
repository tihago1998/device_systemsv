from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.dependencies.auth_dependency import (
    ROLE_ERRORS,
    get_current_active_user,
    require_admin,
    verificar_propietario_o_staff,
)
from app.dependencies.database_dependency import get_db
from app.dependencies.user_dependencies import get_user_or_404, validar_rol
from app.middlewares.rate_limit import LIST_USERS_LIMIT, RATE_LIMIT_ERROR, limiter
from app.models.user_model import User
from app.schemas.device_schema import DeviceResponse
from app.schemas.loan_schema import LoanDetailResponse, LoanStatus
from app.schemas.user_schema import UserCreate, UserPatch, UserResponse, UserUpdate
from app.services import loan_service, user_service

# Todas las rutas de /users exigen un token válido de un usuario activo (401/403 si no).
# Las cabeceras X-App-Name, X-Request-ID, etc. las agrega app/middlewares/request_middleware.py
router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(get_current_active_user)])

ERROR_404 = {404: {"description": "Usuario no encontrado"}}
ERROR_400_EMAIL = {400: {"description": "El correo ya está registrado"}}


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Listar usuarios",
    description=(
        "Lista los usuarios guardados en la base de datos. Permite filtrar por rol y estado, buscar por "
        "nombre o correo, ordenar por id, nombre o fecha de creación, y paginar con skip y limit. "
        "Requiere usuario autenticado. Límite: 30 solicitudes por minuto."
    ),
    response_description="Lista de usuarios que cumplen los filtros aplicados.",
    responses={400: {"description": "Rol no permitido"}, **ROLE_ERRORS, **RATE_LIMIT_ERROR},
)
@limiter.limit(LIST_USERS_LIMIT)
def list_users(
    request: Request,
    role: Optional[str] = Depends(validar_rol),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    search: Optional[str] = Query(None, min_length=2, description="Buscar texto en nombre o correo"),
    order_by: Literal["id", "name", "created_at"] = Query("id", description="Campo por el que se ordena"),
    order: Literal["asc", "desc"] = Query("asc", description="Dirección del orden"),
    skip: int = Query(0, ge=0, description="Cantidad de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Cantidad máxima de registros a devolver"),
    db: Session = Depends(get_db),
):
    return user_service.list_users(db, role, is_active, order_by, order, skip, limit, search)


@router.get(
    "/{user_id}/loans",
    response_model=List[LoanDetailResponse],
    summary="Préstamos de un usuario",
    description=(
        "Historial de préstamos de un usuario, con los datos del dispositivo de cada préstamo (join). "
        "Un usuario con rol user solo puede consultar sus propios préstamos."
    ),
    response_description="Préstamos del usuario, del más reciente al más antiguo.",
    responses={**ERROR_404, **ROLE_ERRORS},
)
def get_user_loans(
    user: User = Depends(get_user_or_404),
    status: Optional[LoanStatus] = Query(None, description="Filtrar por estado del préstamo"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    verificar_propietario_o_staff(current_user, user.id)
    return loan_service.list_loans(db, user_id=user.id, status=status)


@router.get(
    "/{user_id}/devices",
    response_model=List[DeviceResponse],
    summary="Dispositivos asignados a un usuario",
    description=(
        "Dispositivos que el usuario tiene prestados actualmente (préstamos active u overdue). "
        "Con include_returned=true también incluye los que ya devolvió. "
        "Un usuario con rol user solo puede consultar los suyos."
    ),
    response_description="Dispositivos del usuario.",
    responses={**ERROR_404, **ROLE_ERRORS},
)
def get_user_devices(
    user: User = Depends(get_user_or_404),
    include_returned: bool = Query(False, description="Incluir dispositivos de préstamos ya devueltos"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    verificar_propietario_o_staff(current_user, user.id)
    return loan_service.list_devices_of_user(db, user.id, only_active=not include_returned)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Consultar usuario por ID",
    description="Obtiene los datos de un usuario específico a partir de su ID. Requiere usuario autenticado.",
    response_description="Datos del usuario solicitado.",
    responses={**ERROR_404, **ROLE_ERRORS},
)
def get_user(user: User = Depends(get_user_or_404)):
    return user


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    description=(
        "Un admin registra un usuario con cualquier rol, validando que el correo no esté duplicado y que la "
        "contraseña sea segura. La contraseña se guarda como hash. Solo admin."
    ),
    response_description="Usuario creado con su ID y fecha de creación.",
    responses={**ERROR_400_EMAIL, **ROLE_ERRORS},
    dependencies=[Depends(require_admin)],
)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, user.model_dump())


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario (completo)",
    description="Reemplaza todos los datos de un usuario existente. Requiere name, email, role e is_active. Solo admin.",
    response_description="Usuario con los datos actualizados.",
    responses={**ERROR_404, **ERROR_400_EMAIL, **ROLE_ERRORS},
    dependencies=[Depends(require_admin)],
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
    description=(
        "Actualiza solo los campos enviados de un usuario existente. Si no se envía ningún campo responde 400. "
        "Solo admin."
    ),
    response_description="Usuario con los campos actualizados.",
    responses={**ERROR_404, 400: {"description": "Correo duplicado o no se enviaron campos"}, **ROLE_ERRORS},
    dependencies=[Depends(require_admin)],
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
    description="Elimina un usuario existente que no tenga préstamos registrados. Solo admin.",
    response_description="Usuario eliminado exitosamente (sin contenido de respuesta).",
    responses={**ERROR_404, 409: {"description": "El usuario tiene préstamos registrados"}, **ROLE_ERRORS},
    dependencies=[Depends(require_admin)],
)
def remove_user(user: User = Depends(get_user_or_404), db: Session = Depends(get_db)):
    user_service.delete_user(db, user)
    return None
