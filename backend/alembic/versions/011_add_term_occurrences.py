"""add term occurrences

Revision ID: 011
Revises: 010
Create Date: 2026-02-06 12:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create term_occurrences table
    op.create_table(
        "term_occurrences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("term_id", sa.Integer(), nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("frequency", sa.Integer(), nullable=False, default=1),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["term_id"],
            ["glossary_terms.id"],
        ),
        sa.ForeignKeyConstraint(
            ["chapter_id"],
            ["chapters.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Add index and unique constraint
    op.create_index(
        op.f("ix_term_occurrences_project_id"),
        "term_occurrences",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_term_occurrences_term_id"),
        "term_occurrences",
        ["term_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_term_occurrence", "term_occurrences", ["term_id", "chapter_id"]
    )


def downgrade() -> None:
    op.drop_table("term_occurrences")
