"""make hire_date nullable on employee_profiles

Revision ID: e2def12adfb6
Revises: 48d63151957f
Create Date: 2026-07-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2def12adfb6'
down_revision: Union[str, None] = '48d63151957f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('employee_profiles', 'hire_date', existing_type=sa.DateTime(), nullable=True)


def downgrade() -> None:
    op.alter_column('employee_profiles', 'hire_date', existing_type=sa.DateTime(), nullable=False)
