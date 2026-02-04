"""add term relationship indexes

Revision ID: 008
Revises: 007
Create Date: 2025-08-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index('ix_term_relationships_source_term_id', 'term_relationships', ['source_term_id'], unique=False)
    op.create_index('ix_term_relationships_target_term_id', 'term_relationships', ['target_term_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_term_relationships_target_term_id', table_name='term_relationships')
    op.drop_index('ix_term_relationships_source_term_id', table_name='term_relationships')
