"""Add processed_at to chapters

Revision ID: 003
Revises: 002
Create Date: 2025-08-08 13:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add processed_at column to chapters table
    op.add_column('chapters', sa.Column('processed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove processed_at column from chapters table
    op.drop_column('chapters', 'processed_at')
