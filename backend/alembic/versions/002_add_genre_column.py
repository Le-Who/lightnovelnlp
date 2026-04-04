"""Add genre column to projects table

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Column genre is now created in 000_initial.py
    pass


def downgrade() -> None:
    pass
