"""empty message

Revision ID: 3b59ab6d1801
Revises: c5a0631f39b3
Create Date: 2025-08-05 17:46:32.000370

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b59ab6d1801'
down_revision: Union[str, Sequence[str], None] = 'c5a0631f39b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
