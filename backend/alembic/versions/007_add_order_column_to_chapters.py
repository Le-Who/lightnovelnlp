"""add order column to chapters

Revision ID: 007
Revises: 006
Create Date: 2025-08-09 00:00:00.000000
"""

# revision identifiers, used by Alembic.
revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Column order and index are now in 000_initial.py
    pass


def downgrade() -> None:
    pass
