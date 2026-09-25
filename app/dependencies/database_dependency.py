from typing import Iterator

from sqlalchemy.orm import Session

from app.database.connection import get_session


def get_db() -> Iterator[Session]:
    """Dependencia: entrega una sesión de base de datos por petición y la cierra al terminar."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()
