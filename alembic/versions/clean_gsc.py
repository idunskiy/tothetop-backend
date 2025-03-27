"""clean gsc

Revision ID: clean_gsc
Revises: 9901d67c83bd
Create Date: 2024-03-27 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'clean_gsc'
down_revision = '9901d67c83bd'  # Make sure this matches your previous migration
branch_labels = None
depends_on = None

def upgrade():
    # Drop existing constraints if they exist
    op.execute("""
        DO $$
        BEGIN
            BEGIN
                ALTER TABLE gsc_page_data DROP CONSTRAINT IF EXISTS unique_page_data;
            EXCEPTION
                WHEN undefined_object THEN NULL;
            END;
            
            BEGIN
                ALTER TABLE gsc_keyword_data DROP CONSTRAINT IF EXISTS unique_keyword_data;
            EXCEPTION
                WHEN undefined_object THEN NULL;
            END;
        END $$;
    """)

    # Add constraints
    op.create_unique_constraint('unique_page_data', 'gsc_page_data', ['page_url', 'date', 'website_id'])
    op.create_unique_constraint('unique_keyword_data', 'gsc_keyword_data', ['keyword', 'page_url', 'date', 'website_id'])

def downgrade():
    # Drop constraints
    op.drop_constraint('unique_page_data', 'gsc_page_data')
    op.drop_constraint('unique_keyword_data', 'gsc_keyword_data') 