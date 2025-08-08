"""Add approved_at column to glossary_terms

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add approved_at column to glossary_terms table
    op.add_column('glossary_terms', sa.Column('approved_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove approved_at column from glossary_terms table
    op.drop_column('glossary_terms', 'approved_at')
