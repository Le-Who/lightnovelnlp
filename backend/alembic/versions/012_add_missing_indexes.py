"""add missing indexes to glossary terms and batch job items

Revision ID: 012
Revises: 011
Create Date: 2025-05-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add indexes for GlossaryTerm first/last chapter (missing in 010)
    op.create_index(op.f('ix_glossary_terms_first_chapter_id'), 'glossary_terms', ['first_chapter_id'], unique=False)
    op.create_index(op.f('ix_glossary_terms_last_chapter_id'), 'glossary_terms', ['last_chapter_id'], unique=False)

    # Add index for BatchJobItem project_id (missing in 000)
    op.create_index(op.f('ix_batch_job_items_project_id'), 'batch_job_items', ['project_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_batch_job_items_project_id'), table_name='batch_job_items')
    op.drop_index(op.f('ix_glossary_terms_last_chapter_id'), table_name='glossary_terms')
    op.drop_index(op.f('ix_glossary_terms_first_chapter_id'), table_name='glossary_terms')
