"""changed the model for the pgadmin view

Revision ID: 309fa2d722c0
Revises: 5376c1570b3f
Create Date: 2025-07-11 14:25:10.520170

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '309fa2d722c0'
down_revision: Union[str, Sequence[str], None] = '5376c1570b3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'tbl_endorsement_lot_excess', ['tbl_endorsement_t2_ref'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'tbl_endorsement_lot_excess', type_='unique')
    # ### end Alembic commands ###
