"""edited_lot_number_single_for_uniqueness

Revision ID: e7c622ff2ce8
Revises: 4bc3b13d74a1
Create Date: 2025-07-01 14:41:42.695155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7c622ff2ce8'
down_revision: Union[str, Sequence[str], None] = '4bc3b13d74a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'tbl_endorsement_t2', ['t_lotnumbersingle'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'tbl_endorsement_t2', type_='unique')
    # ### end Alembic commands ###
