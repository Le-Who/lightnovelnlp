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
    # Column processed_at is now created in 000_initial.py
    pass


def downgrade() -> None:
    pass
