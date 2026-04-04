"""add indexes and unique constraints

Revision ID: 006
Revises: 005
Create Date: 2025-08-09 00:00:00.000000
"""

# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # All indexes and constraints are now in 000_initial.py
    pass


def downgrade() -> None:
    pass
