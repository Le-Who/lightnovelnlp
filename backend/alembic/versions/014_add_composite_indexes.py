"""add composite indexes

Revision ID: 014
Revises: 013
Create Date: 2026-02-16 12:00:00.000000

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
    op.create_index(op.f('ix_glossary_terms_project_status_created'), 'glossary_terms', ['project_id', 'status', 'created_at'], unique=False)
    op.create_index(op.f('ix_glossary_terms_project_frequency'), 'glossary_terms', ['project_id', 'frequency'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_glossary_terms_project_frequency'), table_name='glossary_terms')
    op.drop_index(op.f('ix_glossary_terms_project_status_created'), table_name='glossary_terms')
