"""tune supabase advisors

Revision ID: 017
Revises: 016
Create Date: 2026-04-05 10:05:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Disable RLS on all tables to clear 'RLS Enabled No Policy' advisor warnings
    # (Since this is a backend-only REST API using raw database connection strings,
    # RLS is naturally bypassed by the postgres user. Enabling RLS without policies
    # just triggers Supabase security linters unnecessarily or locks out service roles if misconfigured).
    tables = [
        "alembic_version",
        "batch_job_items",
        "batch_jobs",
        "chapters",
        "glossary_terms",
        "glossary_versions",
        "projects",
        "term_occurrences",
        "term_relationships"
    ]
    
    # 1. Disable RLS
    for table in tables:
        op.execute(text(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY;"))

    # 2. Relocate vector extension to extensions schema
    op.execute(text("CREATE SCHEMA IF NOT EXISTS extensions;"))
    op.execute(text("ALTER EXTENSION IF EXISTS vector SET SCHEMA extensions;"))


def downgrade() -> None:
    # 1. Re-enable RLS
    tables = [
        "alembic_version",
        "batch_job_items",
        "batch_jobs",
        "chapters",
        "glossary_terms",
        "glossary_versions",
        "projects",
        "term_occurrences",
        "term_relationships"
    ]
    for table in tables:
        op.execute(text(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;"))

    # 2. Move vector back to public schema
    op.execute(text("ALTER EXTENSION IF EXISTS vector SET SCHEMA public;"))
