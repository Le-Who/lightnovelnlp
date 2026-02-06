"""add project_id index to term_relationships

Revision ID: 009
Revises: 008
Create Date: 2024-05-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create index for project_id in term_relationships if it doesn't exist
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    indexes = inspector.get_indexes('term_relationships')
    index_names = [index['name'] for index in indexes]
    
    if 'ix_term_relationships_project_id' not in index_names:
        op.create_index(op.f('ix_term_relationships_project_id'), 'term_relationships', ['project_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_term_relationships_project_id'), table_name='term_relationships')
