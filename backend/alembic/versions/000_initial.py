"""Initial migration - create all tables

Revision ID: 000
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '000'
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(conn, table_name: str) -> bool:
    inspector = Inspector.from_engine(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    conn = op.get_bind()

    # Use raw SQL with IF NOT EXISTS for every table so this migration is
    # fully idempotent against databases that were created before Alembic
    # tracking was introduced.

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            genre VARCHAR(50) NOT NULL DEFAULT 'other',
            created_at TIMESTAMP WITHOUT TIME ZONE
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_projects_id ON projects (id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_projects_name ON projects (name)"))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS chapters (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            title VARCHAR(255) NOT NULL,
            original_text TEXT NOT NULL,
            translated_text TEXT,
            summary TEXT,
            "order" INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITHOUT TIME ZONE,
            processed_at TIMESTAMP WITHOUT TIME ZONE
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_chapters_id ON chapters (id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_chapters_project_id ON chapters (project_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_chapters_order ON chapters (project_id, \"order\")"))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS glossary_terms (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            source_term VARCHAR(255) NOT NULL,
            translated_term VARCHAR(255) NOT NULL,
            category VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            context TEXT,
            frequency INTEGER DEFAULT 1,
            created_at TIMESTAMP WITHOUT TIME ZONE,
            approved_at TIMESTAMP WITHOUT TIME ZONE
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_glossary_terms_id ON glossary_terms (id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_glossary_terms_project_id ON glossary_terms (project_id)"))
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_glossary_term_per_project'
            ) THEN
                ALTER TABLE glossary_terms
                    ADD CONSTRAINT uq_glossary_term_per_project UNIQUE (project_id, source_term);
            END IF;
        END $$;
    """))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS term_relationships (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            source_term_id INTEGER NOT NULL REFERENCES glossary_terms(id),
            target_term_id INTEGER NOT NULL REFERENCES glossary_terms(id),
            relation_type VARCHAR(50) NOT NULL,
            confidence INTEGER,
            context TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_term_relationships_id ON term_relationships (id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_term_relationships_project_id ON term_relationships (project_id)"))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS glossary_versions (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            version_name VARCHAR(255) NOT NULL,
            description TEXT,
            terms_data JSON NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE,
            created_by VARCHAR(100)
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_glossary_versions_id ON glossary_versions (id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_glossary_versions_project_id ON glossary_versions (project_id)"))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS batch_jobs (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            job_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            total_items INTEGER DEFAULT 0,
            processed_items INTEGER DEFAULT 0,
            failed_items INTEGER DEFAULT 0,
            progress_percentage INTEGER DEFAULT 0,
            error_message TEXT,
            job_data JSON,
            created_at TIMESTAMP WITHOUT TIME ZONE,
            started_at TIMESTAMP WITHOUT TIME ZONE,
            completed_at TIMESTAMP WITHOUT TIME ZONE
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_batch_jobs_id ON batch_jobs (id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_batch_jobs_project_id ON batch_jobs (project_id)"))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS batch_job_items (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            batch_job_id INTEGER NOT NULL REFERENCES batch_jobs(id),
            item_type VARCHAR(50) NOT NULL,
            item_id INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            error_message TEXT,
            result JSON,
            started_at TIMESTAMP WITHOUT TIME ZONE,
            completed_at TIMESTAMP WITHOUT TIME ZONE
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_batch_job_items_id ON batch_job_items (id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_batch_job_items_batch_job_id ON batch_job_items (batch_job_id)"))


def downgrade() -> None:
    op.drop_table('batch_job_items')
    op.drop_table('batch_jobs')
    op.drop_table('glossary_versions')
    op.drop_table('term_relationships')
    op.drop_table('glossary_terms')
    op.drop_table('chapters')
    op.drop_table('projects')
