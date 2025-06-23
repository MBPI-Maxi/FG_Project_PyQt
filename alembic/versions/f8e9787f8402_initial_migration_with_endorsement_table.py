"""Initial migration with endorsement table

Revision ID: f8e9787f8402
Revises: f2de5271d2e4
Create Date: 2025-06-23 15:42:03.485772

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8e9787f8402'
down_revision: Union[str, Sequence[str], None] = 'f2de5271d2e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('tbl_endorsement_t1', 'id', new_column_name='t_id')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('tbl_endorsement_t1', 't_id', new_column_name='id')
