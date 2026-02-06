"""add glossary chapter stats

Revision ID: 010
Revises: 009
Create Date: 2026-02-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns for tracking first and last appearance
    op.add_column('glossary_terms', sa.Column('first_chapter_id', sa.Integer(), nullable=True))
    op.add_column('glossary_terms', sa.Column('last_chapter_id', sa.Integer(), nullable=True))
    
    # Create foreign keys
    op.create_foreign_key(None, 'glossary_terms', 'chapters', ['first_chapter_id'], ['id'])
    op.create_foreign_key(None, 'glossary_terms', 'chapters', ['last_chapter_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'glossary_terms', type_='foreignkey')
    op.drop_constraint(None, 'glossary_terms', type_='foreignkey')
    op.drop_column('glossary_terms', 'last_chapter_id')
    op.drop_column('glossary_terms', 'first_chapter_id')
