"""add pages_remaining to user

Revision ID: 57ddaab14cd7
Revises: dceb07905b5d
Create Date: 2025-05-09 06:33:37.223407

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '57ddaab14cd7'
down_revision: Union[str, None] = 'dceb07905b5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('pages_remaining', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'pages_remaining')