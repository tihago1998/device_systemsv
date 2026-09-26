"""Crea el primer usuario administrador desde la terminal.

Uso (con el entorno virtual activo, desde la raíz del proyecto):
    python -m app.auth.create_admin --name "Santiago Varela" --email admin@device.com

La contraseña se pide por teclado (no queda en el historial de la terminal) y se guarda como hash.
Si la terminal no permite escribirla, se puede enviar con --password "MiClave2026".
"""
import argparse
import getpass
import sys

from fastapi import HTTPException
from pydantic import ValidationError

from app.database.connection import get_session
from app.schemas.user_schema import UserCreate
from app.services import user_service


def main() -> None:
    parser = argparse.ArgumentParser(description="Crear un usuario con rol admin")
    parser.add_argument("--name", required=True, help="Nombre completo")
    parser.add_argument("--email", required=True, help="Correo con el que iniciará sesión")
    parser.add_argument(
        "--password",
        help="Contraseña (opcional). Si no se envía, se pide por teclado sin mostrarla en pantalla",
    )
    args = parser.parse_args()

    if args.password:
        password = args.password
    else:
        password = getpass.getpass("Contraseña (no se muestra al escribir): ")
        if password != getpass.getpass("Repita la contraseña: "):
            sys.exit("Las contraseñas no coinciden")

    try:
        data = UserCreate(name=args.name, email=args.email, password=password, role="admin")
    except ValidationError as exc:
        sys.exit("Datos inválidos:\n" + "\n".join(f"- {error['msg']}" for error in exc.errors()))

    db = get_session()
    try:
        user = user_service.create_user(db, data.model_dump())
    except HTTPException as exc:
        sys.exit(exc.detail)
    finally:
        db.close()
    print(f"Administrador creado: id={user.id}, email={user.email}")


if __name__ == "__main__":
    main()
