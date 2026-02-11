"""add index to term occurrences chapter_id

Revision ID: 013
Revises: 012
Create Date: 2026-02-06 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add index for TermOccurrence chapter_id (missing in 011)
    op.create_index(op.f('ix_term_occurrences_chapter_id'), 'term_occurrences', ['chapter_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_term_occurrences_chapter_id'), table_name='term_occurrences')
