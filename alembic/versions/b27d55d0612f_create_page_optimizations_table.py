"""create page optimizations table

Revision ID: b27d55d0612f
Revises: 2e3892380dc6
Create Date: 2025-04-13 14:39:17.971165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b27d55d0612f'
down_revision: Union[str, None] = '2e3892380dc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Drop unused tables
    op.drop_table('website_settings')
    op.drop_table('crawl_sessions')
    op.drop_table('page_improvements')
    op.drop_table('analysis_results')
    
    # Create the page_optimizations table
    op.create_table(
        'page_optimizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('optimization_type', sa.String(10), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=False),
        sa.Column('original_content', sa.Text(), nullable=False),
        sa.Column('modified_content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )

    # Add indexes
    op.create_index('idx_page_optimizations_user_url', 'page_optimizations', ['user_id', 'url'])
    op.create_index('idx_page_optimizations_created_at', 'page_optimizations', ['created_at'])

def downgrade():
    op.drop_index('idx_page_optimizations_created_at')
    op.drop_index('idx_page_optimizations_user_url')
    op.drop_table('page_optimizations')