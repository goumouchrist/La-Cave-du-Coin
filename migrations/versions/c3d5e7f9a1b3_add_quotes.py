"""add quotes

Revision ID: c3d5e7f9a1b3
Revises: a7c9e1f3b5d7
Create Date: 2026-09-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d5e7f9a1b3'
down_revision: Union[str, None] = 'a7c9e1f3b5d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('quotes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('quote_number', sa.String(length=40), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('customer_id', sa.Integer(), nullable=True),
    sa.Column('customer_name', sa.String(length=120), nullable=True),
    sa.Column('customer_phone', sa.String(length=30), nullable=True),
    sa.Column('total_amount', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('EN_COURS', 'CONVERTI', 'ANNULE', 'EXPIRE', name='quotestatus'), nullable=False),
    sa.Column('expires_at', sa.Date(), nullable=True),
    sa.Column('converted_sale_id', sa.Integer(), nullable=True),
    sa.Column('converted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('print_count', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['converted_sale_id'], ['sales.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quotes_quote_number'), 'quotes', ['quote_number'], unique=True)
    op.create_table('quote_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('quote_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('qty_units', sa.Integer(), nullable=False),
    sa.Column('unit_price', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.ForeignKeyConstraint(['quote_id'], ['quotes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('quote_items')
    op.drop_index(op.f('ix_quotes_quote_number'), table_name='quotes')
    op.drop_table('quotes')
