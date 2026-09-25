from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Base de datos SQLite para desarrollo: se crea el archivo device_systems.db en la raíz del proyecto
DATABASE_URL = "sqlite:///./device_systems.db"

# check_same_thread=False: FastAPI puede usar la conexión desde distintos hilos de una misma petición
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Fábrica de sesiones: cada petición abre su propia sesión y la cierra al terminar
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Clase base de la que heredan todos los modelos SQLAlchemy
Base = declarative_base()


def get_session() -> Session:
    """Crea una nueva sesión de base de datos (quien la usa debe cerrarla)."""
    return SessionLocal()
