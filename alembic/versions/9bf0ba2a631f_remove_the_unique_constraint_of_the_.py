"""remove the unique constraint of the endorsement_t2.lotnumbersingle

Revision ID: 9bf0ba2a631f
Revises: 9f059cf22078
Create Date: 2025-07-10 17:09:58.946419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9bf0ba2a631f'
down_revision: Union[str, Sequence[str], None] = '9f059cf22078'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('tbl_endorsement_lot_excess_t_lotnumber_fkey', 'tbl_endorsement_lot_excess', type_='foreignkey')
    
    # 2. Add new integer column for the new foreign key
    op.add_column('tbl_endorsement_lot_excess', 
                 sa.Column('t_lot_id', sa.Integer(), nullable=True))
    
    # 3. Populate the new column with correct t_id values
    op.execute("""
        UPDATE tbl_endorsement_lot_excess le
        SET t_lot_id = t2.t_id
        FROM tbl_endorsement_t2 t2
        WHERE le.t_lotnumber = t2.t_lotnumbersingle
    """)
    
    # 4. Make the new column non-nullable
    op.alter_column('tbl_endorsement_lot_excess', 't_lot_id', nullable=False)
    
    # 5. Create new foreign key
    op.create_foreign_key(
        'tbl_endorsement_lot_excess_t_lot_id_fkey',
        'tbl_endorsement_lot_excess',
        'tbl_endorsement_t2',
        ['t_lot_id'],
        ['t_id']
    )
    
    # 6. Remove the old varchar column (optional - you might want to keep it temporarily)
    op.drop_column('tbl_endorsement_lot_excess', 't_lotnumber')
    
    # 7. Rename the new column to the original name if desired
    op.alter_column('tbl_endorsement_lot_excess', 't_lot_id', new_column_name='t_lotnumber')
    
    # 8. Remove the unique constraints
    op.drop_constraint('tbl_endorsement_t2_t_lotnumbersingle_key', 'tbl_endorsement_t2', type_='unique')
    op.drop_constraint('uq_refno_lot', 'tbl_endorsement_t2', type_='unique')


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Recreate unique constraints
    op.create_unique_constraint('uq_refno_lot', 'tbl_endorsement_t2', ['t_refno', 't_lotnumbersingle'])
    op.create_unique_constraint('tbl_endorsement_t2_t_lotnumbersingle_key', 'tbl_endorsement_t2', ['t_lotnumbersingle'])
    
    # 2. Add back the old varchar column
    op.add_column('tbl_endorsement_lot_excess',
                 sa.Column('t_lotnumber_old', sa.String(10), nullable=True))
    
    # 3. Populate it with data
    op.execute("""
        UPDATE tbl_endorsement_lot_excess le
        SET t_lotnumber_old = t2.t_lotnumbersingle
        FROM tbl_endorsement_t2 t2
        WHERE le.t_lotnumber = t2.t_id
    """)
    
    # 4. Drop the current foreign key
    op.drop_constraint('tbl_endorsement_lot_excess_t_lot_id_fkey', 'tbl_endorsement_lot_excess', type_='foreignkey')
    
    # 5. Drop the integer column
    op.drop_column('tbl_endorsement_lot_excess', 't_lotnumber')
    
    # 6. Rename the old column back
    op.alter_column('tbl_endorsement_lot_excess', 't_lotnumber_old', new_column_name='t_lotnumber')
    
    # 7. Recreate the original foreign key
    op.create_foreign_key(
        'tbl_endorsement_lot_excess_t_lotnumber_fkey',
        'tbl_endorsement_lot_excess',
        'tbl_endorsement_t2',
        ['t_lotnumber'],
        ['t_lotnumbersingle']
    )
    # ### end Alembic commands ###
