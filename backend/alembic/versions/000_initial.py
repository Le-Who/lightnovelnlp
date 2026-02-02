"""Initial migration - create all tables

Revision ID: 000
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(255), unique=True, index=True, nullable=False),
        sa.Column('genre', sa.String(50), nullable=False, server_default='other'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    # Create chapters table
    op.create_table(
        'chapters',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('translated_text', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_chapters_project_id', 'chapters', ['project_id'])
    op.create_index('ix_chapters_order', 'chapters', ['project_id', 'order'])

    # Create glossary_terms table
    op.create_table(
        'glossary_terms',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('source_term', sa.String(255), nullable=False),
        sa.Column('translated_term', sa.String(255), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=True, server_default='pending'),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('frequency', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_glossary_terms_project_id', 'glossary_terms', ['project_id'])
    op.create_unique_constraint('uq_glossary_term_per_project', 'glossary_terms', ['project_id', 'source_term'])

    # Create term_relationships table
    op.create_table(
        'term_relationships',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('source_term_id', sa.Integer(), sa.ForeignKey('glossary_terms.id'), nullable=False),
        sa.Column('target_term_id', sa.Integer(), sa.ForeignKey('glossary_terms.id'), nullable=False),
        sa.Column('relation_type', sa.String(50), nullable=False),
        sa.Column('confidence', sa.Integer(), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_term_relationships_project_id', 'term_relationships', ['project_id'])

    # Create glossary_versions table
    op.create_table(
        'glossary_versions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('version_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('terms_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
    )
    op.create_index('ix_glossary_versions_project_id', 'glossary_versions', ['project_id'])

    # Create batch_jobs table
    op.create_table(
        'batch_jobs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=True, server_default='pending'),
        sa.Column('total_items', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('processed_items', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('failed_items', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('progress_percentage', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('job_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_batch_jobs_project_id', 'batch_jobs', ['project_id'])

    # Create batch_job_items table
    op.create_table(
        'batch_job_items',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('batch_job_id', sa.Integer(), sa.ForeignKey('batch_jobs.id'), nullable=False),
        sa.Column('item_type', sa.String(50), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=True, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_batch_job_items_batch_job_id', 'batch_job_items', ['batch_job_id'])


def downgrade() -> None:
    op.drop_table('batch_job_items')
    op.drop_table('batch_jobs')
    op.drop_table('glossary_versions')
    op.drop_table('term_relationships')
    op.drop_table('glossary_terms')
    op.drop_table('chapters')
    op.drop_table('projects')
