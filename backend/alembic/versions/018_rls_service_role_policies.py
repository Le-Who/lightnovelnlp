"""rls service role policies

Revision ID: 018
Revises: 017
Create Date: 2026-04-05 10:06:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Re-enable RLS on all tables and add a permissive policy for the service_role.
    # This satisfies the Supabase security linter without blocking the backend.
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
        op.execute(text(f"DROP POLICY IF EXISTS \"service_role_all\" ON public.{table};"))
        op.execute(text(
            f"CREATE POLICY \"service_role_all\" ON public.{table} "
            f"AS PERMISSIVE FOR ALL TO service_role USING (true) WITH CHECK (true);"
        ))


def downgrade() -> None:
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
        op.execute(text(f"DROP POLICY IF EXISTS \"service_role_all\" ON public.{table};"))
        op.execute(text(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY;"))
