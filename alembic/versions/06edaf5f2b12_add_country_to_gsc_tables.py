"""add_country_to_gsc_tables

Revision ID: 06edaf5f2b12
Revises: f09b5dfdc8df
Create Date: 2025-03-28 21:22:51.023786

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '06edaf5f2b12'
down_revision: Union[str, None] = 'f09b5dfdc8df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
