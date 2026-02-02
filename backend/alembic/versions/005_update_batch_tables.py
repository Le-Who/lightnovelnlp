"""Add missing columns to batch tables

Revision ID: 005
Revises: 004
Create Date: 2025-01-08 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # All batch columns are now in 000_initial.py
    pass


def downgrade() -> None:
    pass


