from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """Modelo SQLAlchemy: representa la tabla users en la base de datos."""

    __tablename__ = "users"
    __table_args__ = (
        # Constraint a nivel de base de datos: solo se aceptan estos roles
        CheckConstraint("role IN ('admin', 'support', 'user')", name="ck_users_role"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    # One-to-Many: un usuario puede tener muchos préstamos
    loans = relationship("Loan", back_populates="user")
