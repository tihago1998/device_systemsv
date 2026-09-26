from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base
from app.models.user_model import utc_now


class Device(Base):
    """Modelo SQLAlchemy: representa la tabla devices (equipos tecnológicos disponibles para préstamo)."""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    serial_number = Column(String(50), unique=True, nullable=False, index=True)
    device_type = Column(String(30), nullable=False, index=True)
    brand = Column(String(50), nullable=True)
    is_available = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    # One-to-Many: un dispositivo aparece en muchos préstamos históricos
    loans = relationship("Loan", back_populates="device")
