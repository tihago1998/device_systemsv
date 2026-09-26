from datetime import date
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.dependencies.auth_dependency import (
    ROLE_ERRORS,
    get_current_active_user,
    require_admin_or_support,
    verificar_propietario_o_staff,
)
from app.dependencies.database_dependency import get_db
from app.dependencies.loan_dependencies import get_loan_or_404
from app.middlewares.rate_limit import CREATE_LOAN_LIMIT, RATE_LIMIT_ERROR, limiter
from app.models.loan_model import Loan
from app.models.user_model import User
from app.schemas.device_schema import DeviceType
from app.schemas.loan_schema import LoanCreate, LoanDetailResponse, LoanResponse, LoanStatus, LoanUpdate
from app.services import loan_service

# Todas las rutas de /loans exigen un token válido; algunas además requieren rol admin o support
router = APIRouter(prefix="/loans", tags=["Loans"], dependencies=[Depends(get_current_active_user)])

ERROR_404 = {404: {"description": "Préstamo no encontrado"}}


class LoanFilters:
    """Parámetros de consulta compartidos por GET /loans y GET /loans/details."""

    def __init__(
        self,
        status: Optional[LoanStatus] = Query(None, description="Filtrar por estado: active, returned u overdue"),
        user_id: Optional[int] = Query(None, gt=0, description="Filtrar por ID de usuario"),
        device_id: Optional[int] = Query(None, gt=0, description="Filtrar por ID de dispositivo"),
        user_email: Optional[str] = Query(None, description="Filtrar por correo del usuario, p. ej. aprendiz@sena.edu.co"),
        device_type: Optional[DeviceType] = Query(None, description="Filtrar por tipo de dispositivo"),
        date_from: Optional[date] = Query(None, description="Préstamos desde esta fecha (AAAA-MM-DD)"),
        date_to: Optional[date] = Query(None, description="Préstamos hasta esta fecha, inclusive (AAAA-MM-DD)"),
        search: Optional[str] = Query(None, min_length=2, description="Buscar en nombre/correo del usuario o nombre/serial del equipo"),
        order: Literal["asc", "desc"] = Query("desc", description="Orden por fecha de préstamo"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
    ):
        self.params = dict(
            status=status, user_id=user_id, device_id=device_id, user_email=user_email,
            device_type=device_type, date_from=date_from, date_to=date_to, search=search,
            order=order, skip=skip, limit=limit,
        )


FILTER_ERRORS = {400: {"description": "Filtro inválido (date_from mayor que date_to)"}}


@router.get(
    "/",
    response_model=List[LoanResponse],
    summary="Listar préstamos",
    description=(
        "Lista los préstamos registrados. Filtros opcionales por estado, usuario, dispositivo, correo del usuario, "
        "tipo de dispositivo, rango de fechas y búsqueda de texto (usa join con users y devices). "
        "Solo admin o support."
    ),
    response_description="Lista de préstamos que cumplen los filtros.",
    responses={**FILTER_ERRORS, **ROLE_ERRORS},
    dependencies=[Depends(require_admin_or_support)],
)
def list_loans(filters: LoanFilters = Depends(), db: Session = Depends(get_db)):
    return loan_service.list_loans(db, **filters.params)


@router.get(
    "/details",
    response_model=List[LoanDetailResponse],
    summary="Listar préstamos con usuario y dispositivo",
    description=(
        "Igual que GET /loans, pero cada préstamo incluye los datos básicos del usuario y del dispositivo (join). "
        "Solo admin o support."
    ),
    response_description="Préstamos con la información relacionada de usuario y dispositivo.",
    responses={**FILTER_ERRORS, **ROLE_ERRORS},
    dependencies=[Depends(require_admin_or_support)],
)
def list_loan_details(filters: LoanFilters = Depends(), db: Session = Depends(get_db)):
    return loan_service.list_loans(db, **filters.params)


@router.get(
    "/{loan_id}",
    response_model=LoanDetailResponse,
    summary="Consultar préstamo por ID",
    description=(
        "Obtiene un préstamo con los datos de su usuario y su dispositivo. "
        "Un usuario con rol user solo puede consultar sus propios préstamos."
    ),
    response_description="Préstamo con información relacionada.",
    responses={**ERROR_404, **ROLE_ERRORS},
)
def get_loan(loan: Loan = Depends(get_loan_or_404), current_user: User = Depends(get_current_active_user)):
    verificar_propietario_o_staff(current_user, loan.user_id)
    return loan


@router.post(
    "/",
    response_model=LoanDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar préstamo",
    description=(
        "Presta un dispositivo a un usuario. Valida que el usuario exista y esté activo, que el dispositivo exista "
        "y que esté disponible. Al crearlo, el dispositivo queda con is_available = false. "
        "Requiere usuario autenticado: un usuario con rol user solo puede solicitar préstamos a su nombre. "
        "Límite: 10 solicitudes por minuto."
    ),
    response_description="Préstamo creado con los datos del usuario y del dispositivo.",
    responses={
        404: {"description": "Usuario o dispositivo no encontrado"},
        409: {"description": "Dispositivo no disponible o usuario inactivo"},
        **ROLE_ERRORS,
        **RATE_LIMIT_ERROR,
    },
)
@limiter.limit(CREATE_LOAN_LIMIT)
def create_loan(
    request: Request,
    loan: LoanCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    verificar_propietario_o_staff(current_user, loan.user_id)
    return loan_service.create_loan(db, loan.user_id, loan.device_id)


@router.patch(
    "/{loan_id}/return",
    response_model=LoanDetailResponse,
    summary="Devolver dispositivo",
    description=(
        "Registra la devolución del préstamo: estado returned, fecha de devolución actual y el dispositivo "
        "vuelve a quedar disponible. Solo admin o support."
    ),
    response_description="Préstamo devuelto.",
    responses={**ERROR_404, 409: {"description": "El préstamo ya fue devuelto"}, **ROLE_ERRORS},
    dependencies=[Depends(require_admin_or_support)],
)
def return_loan(loan: Loan = Depends(get_loan_or_404), db: Session = Depends(get_db)):
    return loan_service.return_loan(db, loan)


@router.patch(
    "/{loan_id}",
    response_model=LoanDetailResponse,
    summary="Cambiar estado del préstamo",
    description=(
        "Cambia el estado de un préstamo abierto entre active y overdue (vencido). Para devolver use /return. "
        "Solo admin o support."
    ),
    response_description="Préstamo con el estado actualizado.",
    responses={**ERROR_404, 409: {"description": "El préstamo ya fue devuelto"}, **ROLE_ERRORS},
    dependencies=[Depends(require_admin_or_support)],
)
def update_loan(data: LoanUpdate, loan: Loan = Depends(get_loan_or_404), db: Session = Depends(get_db)):
    return loan_service.update_loan_status(db, loan, data.status)
