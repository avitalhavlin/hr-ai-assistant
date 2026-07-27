"""make user_id the pk of employee_profiles

Revision ID: 8d058e9f1ffa
Revises: 48d63151957f
Create Date: 2026-07-27 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d058e9f1ffa'
down_revision: Union[str, None] = '48d63151957f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('employee_profiles_pkey', 'employee_profiles', type_='primary')
    op.drop_constraint('employee_profiles_user_id_key', 'employee_profiles', type_='unique')
    op.drop_column('employee_profiles', 'id')
    op.create_primary_key('employee_profiles_pkey', 'employee_profiles', ['user_id'])


def downgrade() -> None:
    op.drop_constraint('employee_profiles_pkey', 'employee_profiles', type_='primary')
    op.add_column('employee_profiles', sa.Column('id', sa.Integer(), autoincrement=True, nullable=False))
    op.execute(
        "UPDATE employee_profiles SET id = sub.rn "
        "FROM (SELECT user_id, row_number() OVER () AS rn FROM employee_profiles) AS sub "
        "WHERE employee_profiles.user_id = sub.user_id"
    )
    op.create_primary_key('employee_profiles_pkey', 'employee_profiles', ['id'])
    op.create_unique_constraint('employee_profiles_user_id_key', 'employee_profiles', ['user_id'])
