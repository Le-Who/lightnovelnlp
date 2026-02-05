"""add project_id index to term_relationships

Revision ID: 009
Revises: 008
Create Date: 2024-05-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create index for project_id in term_relationships
    op.create_index(op.f('ix_term_relationships_project_id'), 'term_relationships', ['project_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_term_relationships_project_id'), table_name='term_relationships')
