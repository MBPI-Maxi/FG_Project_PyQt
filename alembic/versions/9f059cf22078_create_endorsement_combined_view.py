"""create endorsement_combined view

Revision ID: 9f059cf22078
Revises: 0944c348a592
Create Date: 2025-07-10 10:59:47.191482

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f059cf22078'
down_revision: Union[str, Sequence[str], None] = '0944c348a592'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_views WHERE viewname = 'endorsement_combined' AND schemaname = 'public'
            ) THEN
                EXECUTE '
                    CREATE VIEW public.endorsement_combined AS
                    SELECT
                        t1.t_refno,
                        t1.t_lotnumberwhole AS lot_number,
                        SUM(t2.t_qty) AS total_quantity,
                        t1.t_prodcode,
                        t1.t_status,
                        t1.t_endorsed_by,
                        t1.t_date_endorsed,
                        t1.t_category,
                        t1.t_has_excess
                    FROM tbl_endorsement_t1 t1
                    JOIN tbl_endorsement_t2 t2 ON t1.t_refno::text = t2.t_refno::text
                    GROUP BY
                        t1.t_refno,
                        t1.t_lotnumberwhole,
                        t1.t_prodcode,
                        t1.t_status,
                        t1.t_endorsed_by,
                        t1.t_date_endorsed,
                        t1.t_category,
                        t1.t_has_excess

                    UNION ALL

                    SELECT
                        t2.t_refno,
                        t2.t_lotnumbersingle AS lot_number,
                        t2.t_qty AS total_quantity,
                        t1.t_prodcode,
                        t1.t_status,
                        t1.t_endorsed_by,
                        t1.t_date_endorsed,
                        t1.t_category,
                        t1.t_has_excess
                    FROM tbl_endorsement_t2 t2
                    LEFT JOIN tbl_endorsement_t1 t1 ON t2.t_refno::text = t1.t_refno::text
                ';
            END IF;
        END
        $$;
    """)

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP VIEW IF EXISTS public.endorsement_combined;")
