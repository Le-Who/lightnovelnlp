"""update glossary versions table

Revision ID: 004
Revises: 003
Create Date: 2025-01-08 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Schema is now correct in 000_initial.py (version_name, terms_data)
    pass


def downgrade() -> None:
    pass
