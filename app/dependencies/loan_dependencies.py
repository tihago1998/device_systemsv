from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.models.loan_model import Loan
from app.services import loan_service


def get_loan_or_404(loan_id: int, db: Session = Depends(get_db)) -> Loan:
    """Dependencia reutilizable: obtiene un préstamo de la base de datos o lanza 404."""
    loan = loan_service.get_loan_by_id(db, loan_id)
    if loan is None:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    return loan
