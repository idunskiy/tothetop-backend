"""add_batch_id_to_gsc_tables

Revision ID: 0221dbe40023
Revises: 06edaf5f2b12
Create Date: 2025-03-31 08:15:32.326746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0221dbe40023'
down_revision: Union[str, None] = '06edaf5f2b12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add batch_id column to gsc_page_data
    op.add_column('gsc_page_data', 
        sa.Column('batch_id', sa.String(255), nullable=True)  # Initially allow NULL
    )
    
    # Add batch_id column to gsc_keyword_data
    op.add_column('gsc_keyword_data', 
        sa.Column('batch_id', sa.String(255), nullable=True)  # Initially allow NULL
    )

    # Update existing records with a default batch_id
    op.execute("UPDATE gsc_page_data SET batch_id = 'legacy_batch' WHERE batch_id IS NULL")
    op.execute("UPDATE gsc_keyword_data SET batch_id = 'legacy_batch' WHERE batch_id IS NULL")

    # Make batch_id non-nullable after setting default value
    op.alter_column('gsc_page_data', 'batch_id',
        existing_type=sa.String(255),
        nullable=False
    )
    op.alter_column('gsc_keyword_data', 'batch_id',
        existing_type=sa.String(255),
        nullable=False
    )

    # Drop existing unique constraints
    op.drop_constraint('unique_page_data', 'gsc_page_data', type_='unique')
    op.drop_constraint('unique_keyword_data', 'gsc_keyword_data', type_='unique')

    # Create new unique constraints including batch_id
    op.create_unique_constraint('unique_page_data', 'gsc_page_data', 
        ['page_url', 'date', 'website_id', 'batch_id']
    )
    op.create_unique_constraint('unique_keyword_data', 'gsc_keyword_data', 
        ['keyword', 'page_url', 'date', 'website_id', 'batch_id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop new unique constraints
    op.drop_constraint('unique_page_data', 'gsc_page_data', type_='unique')
    op.drop_constraint('unique_keyword_data', 'gsc_keyword_data', type_='unique')

    # Recreate original unique constraints
    op.create_unique_constraint('unique_page_data', 'gsc_page_data', 
        ['page_url', 'date', 'website_id']
    )
    op.create_unique_constraint('unique_keyword_data', 'gsc_keyword_data', 
        ['keyword', 'page_url', 'date', 'website_id']
    )

    # Drop batch_id columns
    op.drop_column('gsc_page_data', 'batch_id')
    op.drop_column('gsc_keyword_data', 'batch_id')
