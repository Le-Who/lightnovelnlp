"""Add missing columns to batch tables

Revision ID: 005
Revises: 004
Create Date: 2025-01-08 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch_jobs: ensure project_id and total_items exist
    with op.batch_alter_table('batch_jobs') as batch_op:
        try:
            batch_op.add_column(sa.Column('project_id', sa.Integer(), nullable=True))
        except Exception:
            pass
        try:
            batch_op.add_column(sa.Column('total_items', sa.Integer(), nullable=True))
        except Exception:
            pass

    # batch_job_items: ensure project_id and item_type exist
    with op.batch_alter_table('batch_job_items') as batch_op:
        try:
            batch_op.add_column(sa.Column('project_id', sa.Integer(), nullable=True))
        except Exception:
            pass
        try:
            batch_op.add_column(sa.Column('item_type', sa.String(length=50), nullable=True))
        except Exception:
            pass

    # Try to backfill NULLs with defaults where possible
    op.execute("UPDATE batch_jobs SET total_items = COALESCE(total_items, 0)")
    op.execute("UPDATE batch_job_items SET item_type = COALESCE(item_type, 'chapter')")


def downgrade() -> None:
    with op.batch_alter_table('batch_job_items') as batch_op:
        try:
            batch_op.drop_column('item_type')
        except Exception:
            pass
        try:
            batch_op.drop_column('project_id')
        except Exception:
            pass
    with op.batch_alter_table('batch_jobs') as batch_op:
        try:
            batch_op.drop_column('total_items')
        except Exception:
            pass
        try:
            batch_op.drop_column('project_id')
        except Exception:
            pass


