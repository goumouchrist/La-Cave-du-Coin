"""add customer email and email_sent_at to quotes

Revision ID: b7e3d9a5c8f1
Revises: a1c4e7f2b9d6
Create Date: 2026-09-29 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e3d9a5c8f1'
down_revision: Union[str, None] = 'a1c4e7f2b9d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('quotes') as batch_op:
        batch_op.add_column(sa.Column('customer_email', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('email_sent_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('quotes') as batch_op:
        batch_op.drop_column('email_sent_at')
        batch_op.drop_column('customer_email')
