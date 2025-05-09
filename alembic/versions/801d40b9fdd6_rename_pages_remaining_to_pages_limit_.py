"""rename pages_remaining to pages_limit in user

Revision ID: 801d40b9fdd6
Revises: 361486706b9e
Create Date: 2025-05-09 07:14:22.522791

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '801d40b9fdd6'
down_revision: Union[str, None] = '361486706b9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('users', 'pages_remaining', new_column_name='pages_limit')


def downgrade() -> None:
    op.alter_column('users', 'pages_limit', new_column_name='pages_remaining')
