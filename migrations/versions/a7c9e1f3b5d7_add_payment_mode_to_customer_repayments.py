"""add payment mode to customer repayments

Revision ID: a7c9e1f3b5d7
Revises: f1a2b3c4d5e6
Create Date: 2026-09-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c9e1f3b5d7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Reutilise le type ENUM 'paymentmode' deja cree pour sales.payment_mode
# (create_type=False : ne pas tenter de le recreer sur PostgreSQL).
PAYMENT_MODE_ENUM = sa.Enum(
    'ESPECES', 'MOBILE_MONEY', 'CREDIT', 'AVOIR', 'SOUTRA_MONEY', 'CREDIT_MONEY', 'PAYCARD',
    name='paymentmode', create_type=False,
)


def upgrade() -> None:
    with op.batch_alter_table('customer_repayments') as batch_op:
        batch_op.add_column(sa.Column('payment_mode', PAYMENT_MODE_ENUM, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('customer_repayments') as batch_op:
        batch_op.drop_column('payment_mode')
