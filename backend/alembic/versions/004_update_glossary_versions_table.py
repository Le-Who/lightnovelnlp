"""update glossary versions table

Revision ID: 004
Revises: 003
Create Date: 2025-01-08 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Переименовываем version_number в version_name
    op.alter_column('glossary_versions', 'version_number', 
                    new_column_name='version_name', 
                    existing_type=sa.Integer(), 
                    type_=sa.String(255), 
                    existing_nullable=False)
    
    # Переименовываем terms_snapshot в terms_data
    op.alter_column('glossary_versions', 'terms_snapshot', 
                    new_column_name='terms_data', 
                    existing_type=sa.JSON(), 
                    existing_nullable=False)


def downgrade() -> None:
    # Возвращаем обратно terms_data в terms_snapshot
    op.alter_column('glossary_versions', 'terms_data', 
                    new_column_name='terms_snapshot', 
                    existing_type=sa.JSON(), 
                    existing_nullable=False)
    
    # Возвращаем обратно version_name в version_number
    op.alter_column('glossary_versions', 'version_name', 
                    new_column_name='version_number', 
                    existing_type=sa.String(255), 
                    type_=sa.Integer(), 
                    existing_nullable=False)
