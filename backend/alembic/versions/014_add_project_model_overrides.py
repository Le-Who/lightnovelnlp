"""add project model and thinking overrides

Revision ID: 014
Revises: 013
Create Date: 2026-04-04 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Per-project Gemini model overrides (NULL = inherit from ENV/config defaults)
    op.add_column(
        "projects", sa.Column("model_extraction", sa.String(100), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("model_translation", sa.String(100), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("model_summarization", sa.String(100), nullable=True)
    )

    # Per-project thinking level overrides (NULL = inherit from ENV/config defaults)
    op.add_column(
        "projects", sa.Column("thinking_extraction", sa.String(20), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("thinking_translation", sa.String(20), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("projects", "thinking_translation")
    op.drop_column("projects", "thinking_extraction")
    op.drop_column("projects", "model_summarization")
    op.drop_column("projects", "model_translation")
    op.drop_column("projects", "model_extraction")
