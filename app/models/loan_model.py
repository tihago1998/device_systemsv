from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base
from app.models.user_model import utc_now


class Loan(Base):
    """Modelo SQLAlchemy: representa la tabla loans (préstamo de un dispositivo a un usuario)."""

    __tablename__ = "loans"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'returned', 'overdue')", name="ck_loans_status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    # Integridad referencial: el préstamo siempre apunta a un usuario y un dispositivo existentes
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    loan_date = Column(DateTime, nullable=False, default=utc_now)
    return_date = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="active", index=True)

    # Many-to-One: cada préstamo pertenece a un usuario y a un dispositivo
    user = relationship("User", back_populates="loans")
    device = relationship("Device", back_populates="loans")
