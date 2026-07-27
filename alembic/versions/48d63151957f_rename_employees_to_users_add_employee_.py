"""rename employees to users, add employee_profiles

Revision ID: 48d63151957f
Revises: 7f8ad4e24891
Create Date: 2026-07-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48d63151957f'
down_revision: Union[str, None] = '7f8ad4e24891'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table('employees', 'users')

    op.create_table(
        'employee_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('expected_daily_hours', sa.Float(), server_default='8.0', nullable=False),
        sa.Column('hire_date', sa.DateTime(), nullable=False),
        sa.Column('remaining_vacation_days', sa.Float(), server_default='21.0', nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('user_id'),
    )

    # Carry existing per-user data over into the new profile table before
    # dropping the columns from `users`.
    op.execute(
        "INSERT INTO employee_profiles (user_id, expected_daily_hours, hire_date, remaining_vacation_days) "
        "SELECT id, expected_daily_hours, hire_date, 21.0 FROM users"
    )

    op.drop_column('users', 'expected_daily_hours')
    op.drop_column('users', 'hire_date')

    op.alter_column('time_entries', 'employee_id', new_column_name='user_id')
    op.alter_column('vacation_requests', 'employee_id', new_column_name='user_id')


def downgrade() -> None:
    op.alter_column('vacation_requests', 'user_id', new_column_name='employee_id')
    op.alter_column('time_entries', 'user_id', new_column_name='employee_id')

    op.add_column('users', sa.Column('hire_date', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('expected_daily_hours', sa.Float(), server_default='8.0', nullable=False))

    op.execute(
        "UPDATE users SET hire_date = employee_profiles.hire_date, "
        "expected_daily_hours = employee_profiles.expected_daily_hours "
        "FROM employee_profiles WHERE employee_profiles.user_id = users.id"
    )
    op.alter_column('users', 'hire_date', nullable=False)

    op.drop_table('employee_profiles')
    op.rename_table('users', 'employees')
