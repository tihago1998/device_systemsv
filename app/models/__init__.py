# Importar aquí todos los modelos para que queden registrados en Base.metadata
# (Alembic los necesita para detectar las tablas con --autogenerate).
from app.models.user_model import User  # noqa: F401
from app.models.device_model import Device  # noqa: F401
from app.models.loan_model import Loan  # noqa: F401
