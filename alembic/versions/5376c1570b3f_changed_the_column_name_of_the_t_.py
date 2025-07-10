"""changed the column name of the t_lotnumber

Revision ID: 5376c1570b3f
Revises: 9bf0ba2a631f
Create Date: 2025-07-10 17:24:04.083398

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.inspection import inspect


# revision identifiers, used by Alembic.
revision: str = '5376c1570b3f'
down_revision: Union[str, Sequence[str], None] = '9bf0ba2a631f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. First drop the existing foreign key using raw SQL with IF EXISTS
    #    This prevents the transaction from aborting if the constraint doesn't exist.
    op.execute(
        "ALTER TABLE tbl_endorsement_lot_excess DROP CONSTRAINT IF EXISTS tbl_endorsement_lot_excess_t_lotnumber_fkey"
    )
    
    # 2. Add new column with correct INTEGER type
    op.add_column('tbl_endorsement_lot_excess',
                  sa.Column('tbl_endorsement_t2_ref', sa.Integer(), nullable=True))
    
    # 3. Copy data from old column to new column
    op.execute("""
        UPDATE tbl_endorsement_lot_excess le
        SET tbl_endorsement_t2_ref = t2.t_id
        FROM tbl_endorsement_t2 t2
        WHERE le.t_lotnumber = t2.t_id
    """)
    
    # 4. Make the new column non-nullable
    op.alter_column('tbl_endorsement_lot_excess', 'tbl_endorsement_t2_ref', nullable=False)
    
    # 5. Create new foreign key
    op.create_foreign_key(
        'tbl_endorsement_lot_excess_tbl_endorsement_t2_ref_fkey',
        'tbl_endorsement_lot_excess',
        'tbl_endorsement_t2',
        ['tbl_endorsement_t2_ref'],
        ['t_id']
    )
    
    # 6. Drop the old column
    op.drop_column('tbl_endorsement_lot_excess', 't_lotnumber')


def downgrade() -> None:
    # 1. Add back the old column
    op.add_column('tbl_endorsement_lot_excess',
                  sa.Column('t_lotnumber', sa.Integer(), nullable=True))
    
    # 2. Copy data back
    op.execute("""
        UPDATE tbl_endorsement_lot_excess
        SET t_lotnumber = tbl_endorsement_t2_ref
    """)
    
    # 3. Drop the new foreign key
    op.drop_constraint('tbl_endorsement_lot_excess_tbl_endorsement_t2_ref_fkey', 
                       'tbl_endorsement_lot_excess', 
                       type_='foreignkey')
    
    # 4. Drop the new column
    op.drop_column('tbl_endorsement_lot_excess', 'tbl_endorsement_t2_ref')
    
    # 5. Recreate the old foreign key
    #    Use IF EXISTS here as well for robustness during downgrade,
    #    though less likely to be an issue if the upgrade ran successfully.
    op.execute(
        "ALTER TABLE tbl_endorsement_lot_excess ADD CONSTRAINT tbl_endorsement_lot_excess_t_lotnumber_fkey FOREIGN KEY (t_lotnumber) REFERENCES tbl_endorsement_t2 (t_id)"
    )
    # The above op.execute for recreating the foreign key is a direct SQL statement.
    # If you prefer to use op.create_foreign_key, you'd put it back like this:
    # op.create_foreign_key(
    #     'tbl_endorsement_lot_excess_t_lotnumber_fkey',
    #     'tbl_endorsement_lot_excess',
    #     'tbl_endorsement_t2',
    #     ['t_lotnumber'],
    #     ['t_id']
    # )