"""add customer credit sales

Revision ID: b3f9c1e7a2d4
Revises: e26325b85a44
Create Date: 2026-09-10 18:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f9c1e7a2d4'
down_revision: Union[str, None] = 'e26325b85a44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('customers') as batch_op:
        batch_op.add_column(sa.Column('address', sa.String(length=255), nullable=True))
    with op.batch_alter_table('sales') as batch_op:
        batch_op.add_column(sa.Column('remaining_due_gnf', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('due_date', sa.Date(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('sales') as batch_op:
        batch_op.drop_column('due_date')
        batch_op.drop_column('remaining_due_gnf')
    with op.batch_alter_table('customers') as batch_op:
        batch_op.drop_column('address')
