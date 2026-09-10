"""add customer repayments

Revision ID: c7a1d4f6e8b2
Revises: b3f9c1e7a2d4
Create Date: 2026-09-10 19:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7a1d4f6e8b2'
down_revision: Union[str, None] = 'b3f9c1e7a2d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('customer_repayments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('customer_id', sa.Integer(), nullable=False),
    sa.Column('amount_gnf', sa.Integer(), nullable=False),
    sa.Column('processed_by', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
    sa.ForeignKeyConstraint(['processed_by'], ['users.id']),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('customer_repayments')
