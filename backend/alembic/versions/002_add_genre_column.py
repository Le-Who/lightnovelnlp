"""Add genre column to projects table

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add genre column to projects table
    op.add_column('projects', sa.Column('genre', sa.String(50), nullable=False, server_default='other'))


def downgrade() -> None:
    # Remove genre column from projects table
    op.drop_column('projects', 'genre')
