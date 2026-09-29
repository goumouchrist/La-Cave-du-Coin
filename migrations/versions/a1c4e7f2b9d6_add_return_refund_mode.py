"""add refund mode and cash session link to returns

Revision ID: a1c4e7f2b9d6
Revises: d8b4f6a2c1e9
Create Date: 2026-09-29 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c4e7f2b9d6'
down_revision: Union[str, None] = 'd8b4f6a2c1e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Reutilise le type ENUM 'paymentmode' deja cree pour sales.payment_mode
# (create_type=False : ne pas tenter de le recreer sur PostgreSQL).
PAYMENT_MODE_ENUM = sa.Enum(
    'ESPECES', 'MOBILE_MONEY', 'CREDIT', 'AVOIR', 'SOUTRA_MONEY', 'CREDIT_MONEY', 'PAYCARD',
    name='paymentmode', create_type=False,
)


def upgrade() -> None:
    with op.batch_alter_table('returns') as batch_op:
        batch_op.add_column(sa.Column('refund_mode', PAYMENT_MODE_ENUM, nullable=False, server_default='AVOIR'))
        batch_op.add_column(sa.Column('cash_session_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_returns_cash_session_id', 'cash_sessions', ['cash_session_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('returns') as batch_op:
        batch_op.drop_constraint('fk_returns_cash_session_id', type_='foreignkey')
        batch_op.drop_column('cash_session_id')
        batch_op.drop_column('refund_mode')
