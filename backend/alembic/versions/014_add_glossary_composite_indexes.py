"""add glossary composite indexes

Revision ID: 014
Revises: 013
Create Date: 2026-02-06 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add composite indexes for GlossaryTerm
    # For optimize filtering by project and status, and sorting by created_at
    op.create_index('ix_glossary_terms_project_status_created', 'glossary_terms', ['project_id', 'status', 'created_at'], unique=False)

    # For optimize filtering by project and sorting by frequency
    op.create_index('ix_glossary_terms_project_frequency', 'glossary_terms', ['project_id', 'frequency'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_glossary_terms_project_frequency', table_name='glossary_terms')
    op.drop_index('ix_glossary_terms_project_status_created', table_name='glossary_terms')
