"""add stock movement expiry date

Revision ID: d8b4f6a2c1e9
Revises: c3d5e7f9a1b3
Create Date: 2026-09-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8b4f6a2c1e9'
down_revision: Union[str, None] = 'c3d5e7f9a1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('stock_movements') as batch_op:
        batch_op.add_column(sa.Column('expiry_date', sa.Date(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('stock_movements') as batch_op:
        batch_op.drop_column('expiry_date')
