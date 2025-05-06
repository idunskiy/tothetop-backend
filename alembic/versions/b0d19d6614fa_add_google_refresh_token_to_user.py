"""add_google_refresh_token_to_user

Revision ID: b0d19d6614fa
Revises: fd55bd014612
Create Date: 2025-05-05 08:38:59.805051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b0d19d6614fa'
down_revision: Union[str, None] = 'fd55bd014612'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('google_refresh_token', sa.String(length=512), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'google_refresh_token')
