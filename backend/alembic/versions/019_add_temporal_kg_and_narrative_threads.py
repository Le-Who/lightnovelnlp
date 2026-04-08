"""Add temporal KG columns + narrative thread tables

Revision ID: 019
Revises: 018
Create Date: 2026-04-08 01:00:00.000000

Changes:
  - term_relationships: add source_chapter_id, valid_from_chapter, valid_to_chapter,
    superseded_by_id (temporal validity for MemPalace-style KG)
  - narrative_threads: new table for cross-chapter plot arcs
  - thread_anchors: new table for chapter attachment points within a thread
  - RLS policies for new tables via service_role
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Temporal columns on term_relationships ────────────────────────────
    op.execute(text(
        "ALTER TABLE term_relationships "
        "ADD COLUMN IF NOT EXISTS source_chapter_id INTEGER REFERENCES chapters(id)"
    ))
    op.execute(text(
        "ALTER TABLE term_relationships "
        "ADD COLUMN IF NOT EXISTS valid_from_chapter INTEGER"
    ))
    op.execute(text(
        "ALTER TABLE term_relationships "
        "ADD COLUMN IF NOT EXISTS valid_to_chapter INTEGER"
    ))
    op.execute(text(
        "ALTER TABLE term_relationships "
        "ADD COLUMN IF NOT EXISTS superseded_by_id INTEGER "
        "REFERENCES term_relationships(id)"
    ))

    # Index for temporal range lookups
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_tr_temporal "
        "ON term_relationships (valid_from_chapter, valid_to_chapter)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_tr_source_chapter "
        "ON term_relationships (source_chapter_id)"
    ))

    # ── 2. narrative_threads table ───────────────────────────────────────────
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS narrative_threads (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            thread_name VARCHAR(255) NOT NULL,
            thread_type VARCHAR(50) DEFAULT 'plot',
            is_auto_detected INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_narrative_threads_project "
        "ON narrative_threads (project_id)"
    ))

    # ── 3. thread_anchors table ──────────────────────────────────────────────
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS thread_anchors (
            id SERIAL PRIMARY KEY,
            thread_id INTEGER NOT NULL REFERENCES narrative_threads(id) ON DELETE CASCADE,
            chapter_id INTEGER NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
            term_id INTEGER REFERENCES glossary_terms(id) ON DELETE SET NULL,
            anchor_text TEXT,
            anchor_type VARCHAR(50) DEFAULT 'mention',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_thread_anchors_thread "
        "ON thread_anchors (thread_id)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_thread_anchors_chapter "
        "ON thread_anchors (chapter_id)"
    ))

    # ── 4. RLS policies for new tables ──────────────────────────────────────
    new_tables = ["narrative_threads", "thread_anchors"]
    for table in new_tables:
        op.execute(text(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;"))
        op.execute(text(
            f"DROP POLICY IF EXISTS \"service_role_all\" ON public.{table};"
        ))
        op.execute(text(
            f"CREATE POLICY \"service_role_all\" ON public.{table} "
            f"AS PERMISSIVE FOR ALL TO service_role USING (true) WITH CHECK (true);"
        ))


def downgrade() -> None:
    # Remove RLS
    for table in ["narrative_threads", "thread_anchors"]:
        op.execute(text(
            f"DROP POLICY IF EXISTS \"service_role_all\" ON public.{table};"
        ))

    # Drop new tables
    op.execute(text("DROP TABLE IF EXISTS thread_anchors CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS narrative_threads CASCADE"))

    # Drop temporal indexes
    op.execute(text("DROP INDEX IF EXISTS ix_tr_temporal"))
    op.execute(text("DROP INDEX IF EXISTS ix_tr_source_chapter"))

    # Drop temporal columns from term_relationships
    op.execute(text(
        "ALTER TABLE term_relationships DROP COLUMN IF EXISTS superseded_by_id"
    ))
    op.execute(text(
        "ALTER TABLE term_relationships DROP COLUMN IF EXISTS valid_to_chapter"
    ))
    op.execute(text(
        "ALTER TABLE term_relationships DROP COLUMN IF EXISTS valid_from_chapter"
    ))
    op.execute(text(
        "ALTER TABLE term_relationships DROP COLUMN IF EXISTS source_chapter_id"
    ))
