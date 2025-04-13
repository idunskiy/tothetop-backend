"""change optimization_type string lentght in page_optimizations

Revision ID: 62f71df3a4c0
Revises: b27d55d0612f
Create Date: 2025-04-13 21:37:46.432270

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62f71df3a4c0'
down_revision: Union[str, None] = 'b27d55d0612f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.alter_column('page_optimizations', 'optimization_type',
                    type_=sa.Text(),  # Change to Text type which has no length limit
                    existing_type=sa.String(10),
                    existing_nullable=False)

def downgrade():
    op.alter_column('page_optimizations', 'optimization_type',
                    type_=sa.String(10),
                    existing_type=sa.Text(),
                    existing_nullable=False)