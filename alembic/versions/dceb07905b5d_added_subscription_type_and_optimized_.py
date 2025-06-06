"""Added subscription_type and optimized_pages_count fields

Revision ID: dceb07905b5d
Revises: b0d19d6614fa
Create Date: 2025-05-06 14:08:32.207293

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'dceb07905b5d'
down_revision: Union[str, None] = 'b0d19d6614fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('subscription_type', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('optimized_pages_count', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'optimized_pages_count')
    op.drop_column('users', 'subscription_type')
    # ### end Alembic commands ###
