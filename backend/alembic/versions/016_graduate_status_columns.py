"""add status tracking columns to chapters and projects

Revision ID: 016
Revises: 015
Create Date: 2026-04-04 07:15:00.000000

Graduates the columns previously managed by `run_migrations()` in main.py
into the proper Alembic lineage. After this migration is applied, the
`run_migrations()` function in main.py becomes a safe no-op for these columns
(it uses ADD COLUMN IF NOT EXISTS).

Columns added:
  chapters:
    - analysis_status   VARCHAR(20) DEFAULT 'idle' NOT NULL
    - analysis_error    TEXT
    - translation_status VARCHAR(20) DEFAULT 'idle' NOT NULL
    - translation_error TEXT

  projects:
    - source_language          VARCHAR(10) DEFAULT 'en' NOT NULL
    - target_language          VARCHAR(10) DEFAULT 'ru' NOT NULL
    - custom_genre_instructions TEXT
    - embedding_threshold       FLOAT
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def _column_exists(conn, table: str, column: str) -> bool:
    result = conn.execute(
        text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :tbl AND column_name = :col"
        ),
        {"tbl": table, "col": column},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # ── chapters ─────────────────────────────────────────────────────────────
    if not _column_exists(conn, "chapters", "analysis_status"):
        op.add_column(
            "chapters",
            sa.Column(
                "analysis_status",
                sa.String(20),
                nullable=False,
                server_default="idle",
            ),
        )
    if not _column_exists(conn, "chapters", "analysis_error"):
        op.add_column(
            "chapters",
            sa.Column("analysis_error", sa.Text(), nullable=True),
        )
    if not _column_exists(conn, "chapters", "translation_status"):
        op.add_column(
            "chapters",
            sa.Column(
                "translation_status",
                sa.String(20),
                nullable=False,
                server_default="idle",
            ),
        )
    if not _column_exists(conn, "chapters", "translation_error"):
        op.add_column(
            "chapters",
            sa.Column("translation_error", sa.Text(), nullable=True),
        )

    # ── projects ──────────────────────────────────────────────────────────────
    if not _column_exists(conn, "projects", "source_language"):
        op.add_column(
            "projects",
            sa.Column(
                "source_language",
                sa.String(10),
                nullable=False,
                server_default="en",
            ),
        )
    if not _column_exists(conn, "projects", "target_language"):
        op.add_column(
            "projects",
            sa.Column(
                "target_language",
                sa.String(10),
                nullable=False,
                server_default="ru",
            ),
        )
    if not _column_exists(conn, "projects", "custom_genre_instructions"):
        op.add_column(
            "projects",
            sa.Column("custom_genre_instructions", sa.Text(), nullable=True),
        )
    if not _column_exists(conn, "projects", "embedding_threshold"):
        op.add_column(
            "projects",
            sa.Column("embedding_threshold", sa.Float(), nullable=True),
        )


def downgrade() -> None:
    # ── projects ──────────────────────────────────────────────────────────────
    op.drop_column("projects", "embedding_threshold")
    op.drop_column("projects", "custom_genre_instructions")
    op.drop_column("projects", "target_language")
    op.drop_column("projects", "source_language")

    # ── chapters ─────────────────────────────────────────────────────────────
    op.drop_column("chapters", "translation_error")
    op.drop_column("chapters", "translation_status")
    op.drop_column("chapters", "analysis_error")
    op.drop_column("chapters", "analysis_status")
