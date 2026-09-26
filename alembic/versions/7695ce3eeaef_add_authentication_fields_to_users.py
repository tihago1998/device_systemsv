"""add authentication fields to users

Revision ID: 7695ce3eeaef
Revises: 46413d96466f
Create Date: 2026-09-25 22:26:47.744026

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext


# revision identifiers, used by Alembic.
revision: str = '7695ce3eeaef'
down_revision: Union[str, Sequence[str], None] = '46413d96466f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Los usuarios que ya existían no tienen contraseña: se les asigna esta contraseña temporal (solo desarrollo)
# para que la columna pueda ser NOT NULL y esos usuarios puedan iniciar sesión.
TEMP_PASSWORD = "Temporal2026"


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Se agrega la columna permitiendo NULL, porque la tabla ya tiene registros
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('hashed_password', sa.String(length=255), nullable=True))

    # 2. Se guarda el hash bcrypt de la contraseña temporal en los usuarios existentes
    temp_hash = CryptContext(schemes=["bcrypt"], deprecated="auto").hash(TEMP_PASSWORD)
    op.execute(
        sa.text("UPDATE users SET hashed_password = :hash WHERE hashed_password IS NULL").bindparams(hash=temp_hash)
    )

    # 3. Ahora sí la columna se vuelve obligatoria, igual que en el modelo User
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('hashed_password', existing_type=sa.String(length=255), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('hashed_password')
