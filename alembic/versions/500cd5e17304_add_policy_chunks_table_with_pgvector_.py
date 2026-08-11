"""add policy_chunks table with pgvector extension

Revision ID: 500cd5e17304
Revises: e2def12adfb6
Create Date: 2026-08-11 10:59:23.609146

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from app.core.config import settings


# revision identifiers, used by Alembic.
revision: str = '500cd5e17304'
down_revision: Union[str, None] = 'e2def12adfb6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.create_table(
        'policy_chunks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(settings.embedding_dimensions), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('policy_chunks')
    op.execute('DROP EXTENSION IF EXISTS vector')
