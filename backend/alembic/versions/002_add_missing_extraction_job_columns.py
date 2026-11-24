"""Add missing extraction job columns

Revision ID: 002_extraction_cols
Revises: 001_initial_schema
Create Date: 2026-11-24 08:50:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '002_extraction_cols'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Adiciona colunas que faltavam no extraction_jobs
    op.add_column('extraction_jobs', sa.Column('source', sa.String(length=50), nullable=True, server_default='google_scraper'))
    op.add_column('extraction_jobs', sa.Column('auto_import', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('extraction_jobs', sa.Column('extracted_items', sa.JSON(), nullable=True))

def downgrade() -> None:
    op.drop_column('extraction_jobs', 'extracted_items')
    op.drop_column('extraction_jobs', 'auto_import')
    op.drop_column('extraction_jobs', 'source')
