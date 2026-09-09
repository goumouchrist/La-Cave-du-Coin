"""add suppliers

Revision ID: 9ab15f641c93
Revises: 209129f82f57
Create Date: 2026-09-09 19:18:11.315907

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ab15f641c93'
down_revision: Union[str, None] = '209129f82f57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('suppliers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('phone', sa.String(length=30), nullable=True),
    sa.Column('address', sa.String(length=255), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('supplier_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_products_supplier_id', 'suppliers', ['supplier_id'], ['id'])
    with op.batch_alter_table('stock_movements') as batch_op:
        batch_op.add_column(sa.Column('supplier_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_stock_movements_supplier_id', 'suppliers', ['supplier_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('stock_movements') as batch_op:
        batch_op.drop_constraint('fk_stock_movements_supplier_id', type_='foreignkey')
        batch_op.drop_column('supplier_id')
    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_constraint('fk_products_supplier_id', type_='foreignkey')
        batch_op.drop_column('supplier_id')
    op.drop_table('suppliers')
