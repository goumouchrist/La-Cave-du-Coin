"""add sale receipt email tracking

Revision ID: f1a2b3c4d5e6
Revises: d4e6a9c1b3f7
Create Date: 2026-09-18 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'd4e6a9c1b3f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('sales') as batch_op:
        batch_op.add_column(sa.Column('customer_email', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('receipt_email_sent_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('sales') as batch_op:
        batch_op.drop_column('receipt_email_sent_at')
        batch_op.drop_column('customer_email')
