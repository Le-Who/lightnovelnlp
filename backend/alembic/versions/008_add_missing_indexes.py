"""add missing indexes

Revision ID: 008
Revises: 007
Create Date: 2024-05-22 12:00:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create indexes for term_relationships
    op.create_index(
        op.f("ix_term_relationships_source_term_id"),
        "term_relationships",
        ["source_term_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_term_relationships_target_term_id"),
        "term_relationships",
        ["target_term_id"],
        unique=False,
    )

    # Note: batch_job_items.batch_job_id index is NOT created here because
    # it was already created in 000_initial.py (ix_batch_job_items_batch_job_id),
    # even though it was missing from the SQLAlchemy model definition.


def downgrade() -> None:
    op.drop_index(
        op.f("ix_term_relationships_target_term_id"), table_name="term_relationships"
    )
    op.drop_index(
        op.f("ix_term_relationships_source_term_id"), table_name="term_relationships"
    )
