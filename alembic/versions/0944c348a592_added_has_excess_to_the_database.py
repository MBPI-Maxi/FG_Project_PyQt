"""added has excess to the database

Revision ID: 0944c348a592
Revises: bc202fb730c1
Create Date: 2025-07-09 09:04:47.661280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0944c348a592'
down_revision: Union[str, Sequence[str], None] = 'bc202fb730c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "tbl_endorsement_t1",
        sa.Column("t_has_excess", sa.Boolean(), nullable=False, server_default=sa.text("false"))
    )
    op.alter_column("tbl_endorsement_t1", "t_has_excess", server_default=None)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tbl_endorsement_t1', 't_has_excess')
    # ### end Alembic commands ###
