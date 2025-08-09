"""add indexes and unique constraints

Revision ID: 006_indexes_and_unique
Revises: 005_update_batch_tables
Create Date: 2025-08-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_indexes_and_unique'
down_revision = '005_update_batch_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Indexes
    op.create_index('ix_chapters_project_id', 'chapters', ['project_id'], unique=False)
    op.create_index('ix_glossary_terms_project_id', 'glossary_terms', ['project_id'], unique=False)

    # Unique constraint for glossary term per project
    # First ensure no duplicates exist (safe no-op if none)
    # Depending on production data, a data migration might be required; here we assume clean state
    op.create_unique_constraint('uq_glossary_term_per_project', 'glossary_terms', ['project_id', 'source_term'])


def downgrade() -> None:
    op.drop_constraint('uq_glossary_term_per_project', 'glossary_terms', type_='unique')
    op.drop_index('ix_glossary_terms_project_id', table_name='glossary_terms')
    op.drop_index('ix_chapters_project_id', table_name='chapters')


