"""add pgvector extension and embedding column

Revision ID: 015
Revises: 014
Create Date: 2026-04-04 00:10:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension (requires superuser or rds_superuser)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add embedding column to glossary_terms (768-dim, matching gemini-embedding-2-preview MRL output)
    op.add_column(
        "glossary_terms", sa.Column("embedding", sa.LargeBinary(), nullable=True)
    )
    # Note: We store the vector as LargeBinary for portability.
    # For production pgvector queries, use raw SQL with vector(768) type.
    # The actual vector type is created via raw SQL below for full pgvector support.

    # Add the native pgvector column (requires pgvector extension)
    op.execute("""
        ALTER TABLE glossary_terms
        ADD COLUMN IF NOT EXISTS embedding_vec vector(768)
    """)

    # Index for approximate nearest neighbor search (ivfflat or hnsw)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_glossary_terms_embedding_vec
        ON glossary_terms
        USING hnsw (embedding_vec vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_glossary_terms_embedding_vec")
    op.execute("ALTER TABLE glossary_terms DROP COLUMN IF EXISTS embedding_vec")
    op.drop_column("glossary_terms", "embedding")
    op.execute("DROP EXTENSION IF EXISTS vector")
