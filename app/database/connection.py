import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Base de datos SQLite para desarrollo: se crea el archivo device_systems.db en la raíz del proyecto.
# Se puede cambiar con la variable de entorno DATABASE_URL (la usa también Alembic en alembic/env.py).
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./device_systems.db")

# check_same_thread=False: FastAPI puede usar la conexión desde distintos hilos de una misma petición
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def activar_llaves_foraneas(dbapi_connection, connection_record):
    """SQLite no valida las llaves foráneas por defecto: se activan en cada conexión (integridad referencial)."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Fábrica de sesiones: cada petición abre su propia sesión y la cierra al terminar
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Clase base de la que heredan todos los modelos SQLAlchemy
Base = declarative_base()


def get_session() -> Session:
    """Crea una nueva sesión de base de datos (quien la usa debe cerrarla)."""
    return SessionLocal()
