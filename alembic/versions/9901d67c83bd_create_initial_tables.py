"""Create initial tables

Revision ID: 9901d67c83bd
Revises: 
Create Date: 2025-03-27 09:14:24.699868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9901d67c83bd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('google_id', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('google_id')
    )
    op.create_table('websites',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('domain', sa.String(length=255), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=True),
    sa.Column('verification_method', sa.String(length=50), nullable=True),
    sa.Column('added_at', sa.DateTime(), nullable=True),
    sa.Column('last_synced_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('analysis_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('website_id', sa.Integer(), nullable=True),
    sa.Column('overall_score', sa.Integer(), nullable=True),
    sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('analyzed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['website_id'], ['websites.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('crawl_sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('website_id', sa.Integer(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('pages_found', sa.Integer(), nullable=True),
    sa.Column('pages_crawled', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['website_id'], ['websites.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('crawler_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('website_id', sa.Integer(), nullable=True),
    sa.Column('page_url', sa.Text(), nullable=False),
    sa.Column('title', sa.Text(), nullable=True),
    sa.Column('meta_description', sa.Text(), nullable=True),
    sa.Column('h1', sa.Text(), nullable=True),
    sa.Column('h2', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('h3', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('body_text', sa.Text(), nullable=True),
    sa.Column('word_count', sa.Integer(), nullable=True),
    sa.Column('crawled_at', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['website_id'], ['websites.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('gsc_keyword_data',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('website_id', sa.Integer(), nullable=True),
    sa.Column('page_url', sa.Text(), nullable=False),
    sa.Column('keyword', sa.Text(), nullable=False),
    sa.Column('clicks', sa.Integer(), nullable=True),
    sa.Column('impressions', sa.Integer(), nullable=True),
    sa.Column('ctr', sa.Float(), nullable=True),
    sa.Column('average_position', sa.Float(), nullable=True),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['website_id'], ['websites.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('gsc_page_data',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('website_id', sa.Integer(), nullable=True),
    sa.Column('page_url', sa.Text(), nullable=False),
    sa.Column('clicks', sa.Integer(), nullable=True),
    sa.Column('impressions', sa.Integer(), nullable=True),
    sa.Column('ctr', sa.Float(), nullable=True),
    sa.Column('average_position', sa.Float(), nullable=True),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['website_id'], ['websites.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('page_improvements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('website_id', sa.Integer(), nullable=True),
    sa.Column('page_url', sa.Text(), nullable=False),
    sa.Column('improvement_type', sa.String(length=50), nullable=True),
    sa.Column('priority', sa.String(length=20), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['website_id'], ['websites.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('website_settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('website_id', sa.Integer(), nullable=True),
    sa.Column('crawl_frequency', sa.String(length=50), nullable=True),
    sa.Column('excluded_paths', sa.ARRAY(sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['website_id'], ['websites.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('website_settings')
    op.drop_table('page_improvements')
    op.drop_table('gsc_page_data')
    op.drop_table('gsc_keyword_data')
    op.drop_table('crawler_results')
    op.drop_table('crawl_sessions')
    op.drop_table('analysis_results')
    op.drop_table('websites')
    op.drop_table('users')
    # ### end Alembic commands ###
