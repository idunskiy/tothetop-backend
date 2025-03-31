"""add_batch_id_to_crawler_results

Revision ID: 0f2d8c34c107
Revises: 0221dbe40023
Create Date: 2025-03-31 08:48:26.548637

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f2d8c34c107'
down_revision: Union[str, None] = '0221dbe40023'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add batch_id column to crawler_results
    op.add_column('crawler_results', 
        sa.Column('batch_id', sa.String(255), nullable=True)  # Initially allow NULL
    )
    
    # Update existing records with a default batch_id
    op.execute("UPDATE crawler_results SET batch_id = 'legacy_batch' WHERE batch_id IS NULL")

    # Make batch_id non-nullable after setting default value
    op.alter_column('crawler_results', 'batch_id',
        existing_type=sa.String(255),
        nullable=False
    )

def downgrade():
    # Remove batch_id column
    op.drop_column('crawler_results', 'batch_id')
