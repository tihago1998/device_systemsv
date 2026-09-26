from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth_dependency import ROLE_ERRORS, require_admin, require_admin_or_support
from app.dependencies.database_dependency import get_db
from app.dependencies.device_dependencies import get_device_or_404
from app.models.device_model import Device
from app.schemas.device_schema import DeviceCreate, DevicePatch, DeviceResponse, DeviceType, DeviceUpdate
from app.schemas.loan_schema import LoanDetailResponse, LoanStatus
from app.services import device_service, loan_service

# Consultar el catálogo de dispositivos es público; crear, modificar y eliminar requiere rol (ver cada ruta)
router = APIRouter(prefix="/devices", tags=["Devices"])

ERROR_404 = {404: {"description": "Dispositivo no encontrado"}}
ERROR_400_SERIAL = {400: {"description": "El número de serie ya está registrado"}}


@router.get(
    "/",
    response_model=List[DeviceResponse],
    summary="Listar dispositivos",
    description=(
        "Lista los dispositivos registrados. Filtros opcionales: tipo, disponibilidad, marca "
        "(sin distinguir mayúsculas) y búsqueda de texto en nombre, serial o marca. "
        "Permite ordenar y paginar."
    ),
    response_description="Lista de dispositivos que cumplen los filtros aplicados.",
)
def list_devices(
    device_type: Optional[DeviceType] = Query(None, description="Filtrar por tipo de dispositivo"),
    is_available: Optional[bool] = Query(None, description="Filtrar por disponibilidad"),
    brand: Optional[str] = Query(None, description="Filtrar por marca, p. ej. lenovo"),
    search: Optional[str] = Query(None, min_length=2, description="Buscar texto en nombre, serial o marca, p. ej. thinkpad"),
    order_by: Literal["id", "name", "created_at"] = Query("id", description="Campo por el que se ordena"),
    order: Literal["asc", "desc"] = Query("asc", description="Dirección del orden"),
    skip: int = Query(0, ge=0, description="Cantidad de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Cantidad máxima de registros a devolver"),
    db: Session = Depends(get_db),
):
    return device_service.list_devices(db, device_type, is_available, brand, search, order_by, order, skip, limit)


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Consultar dispositivo por ID",
    description="Obtiene los datos de un dispositivo específico a partir de su ID.",
    response_description="Datos del dispositivo solicitado.",
    responses=ERROR_404,
)
def get_device(device: Device = Depends(get_device_or_404)):
    return device


@router.get(
    "/{device_id}/loans",
    response_model=List[LoanDetailResponse],
    summary="Historial de préstamos de un dispositivo",
    description=(
        "Todos los préstamos en los que ha participado el dispositivo, con los datos del usuario (join). "
        "Solo admin o support."
    ),
    response_description="Historial de préstamos del dispositivo, del más reciente al más antiguo.",
    responses={**ERROR_404, **ROLE_ERRORS},
    dependencies=[Depends(require_admin_or_support)],
)
def get_device_loans(
    device: Device = Depends(get_device_or_404),
    status: Optional[LoanStatus] = Query(None, description="Filtrar por estado del préstamo"),
    db: Session = Depends(get_db),
):
    return loan_service.list_loans(db, device_id=device.id, status=status)


@router.post(
    "/",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar dispositivo",
    description=(
        "Registra un nuevo equipo tecnológico, validando que el número de serie no esté duplicado. "
        "Solo admin o support."
    ),
    response_description="Dispositivo creado con su ID y fecha de creación.",
    responses={**ERROR_400_SERIAL, **ROLE_ERRORS},
    dependencies=[Depends(require_admin_or_support)],
)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    return device_service.create_device(db, device.model_dump())


@router.put(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Actualizar dispositivo (completo)",
    description="Reemplaza todos los datos de un dispositivo existente. Solo admin o support.",
    response_description="Dispositivo con los datos actualizados.",
    responses={
        **ERROR_404,
        **ERROR_400_SERIAL,
        409: {"description": "No se puede marcar como disponible un equipo con préstamo activo"},
        **ROLE_ERRORS,
    },
    dependencies=[Depends(require_admin_or_support)],
)
def update_device(
    device: DeviceUpdate,
    current_device: Device = Depends(get_device_or_404),
    db: Session = Depends(get_db),
):
    return device_service.update_device_full(db, current_device, device.model_dump())


@router.patch(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Actualizar dispositivo (parcial)",
    description="Actualiza solo los campos enviados. Si no se envía ningún campo responde 400. Solo admin o support.",
    response_description="Dispositivo con los campos actualizados.",
    responses={
        **ERROR_404,
        400: {"description": "Serial duplicado o no se enviaron campos"},
        409: {"description": "No se puede marcar como disponible un equipo con préstamo activo"},
        **ROLE_ERRORS,
    },
    dependencies=[Depends(require_admin_or_support)],
)
def patch_device(
    device: DevicePatch,
    current_device: Device = Depends(get_device_or_404),
    db: Session = Depends(get_db),
):
    # exclude_none: los campos enviados como null se ignoran (brand se limpia con PUT)
    fields = device.model_dump(exclude_unset=True, exclude_none=True)
    return device_service.update_device_partial(db, current_device, fields)


@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar dispositivo",
    description="Elimina un dispositivo que no tenga préstamos registrados. Solo admin.",
    response_description="Dispositivo eliminado exitosamente (sin contenido de respuesta).",
    responses={**ERROR_404, 409: {"description": "El dispositivo tiene préstamos registrados"}, **ROLE_ERRORS},
    dependencies=[Depends(require_admin)],
)
def remove_device(device: Device = Depends(get_device_or_404), db: Session = Depends(get_db)):
    device_service.delete_device(db, device)
    return None
