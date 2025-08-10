"""add order column to chapters

Revision ID: 007
Revises: 006
Create Date: 2025-08-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add order column to chapters table
    op.add_column('chapters', sa.Column('order', sa.Integer(), nullable=False, server_default='0'))
    
    # Create index for efficient ordering
    op.create_index('ix_chapters_order', 'chapters', ['project_id', 'order'], unique=False)


def downgrade() -> None:
    # Drop index first
    op.drop_index('ix_chapters_order', table_name='chapters')
    
    # Drop order column
    op.drop_column('chapters', 'order')
