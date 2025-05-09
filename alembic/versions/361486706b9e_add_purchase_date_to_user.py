"""add purchase_date to user

Revision ID: 361486706b9e
Revises: 57ddaab14cd7
Create Date: 2025-05-09 06:36:58.013937

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '361486706b9e'
down_revision: Union[str, None] = '57ddaab14cd7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('purchase_date', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'purchase_date')
