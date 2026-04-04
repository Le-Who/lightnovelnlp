"""Add approved_at column to glossary_terms

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = "001"
down_revision = "000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Column approved_at is now created in 000_initial.py
    # This migration kept for chain compatibility
    pass


def downgrade() -> None:
    # Column approved_at is now handled in 000_initial.py
    pass
