"""add cash session resolution

Revision ID: d4e6a9c1b3f7
Revises: c7a1d4f6e8b2
Create Date: 2026-09-11 09:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e6a9c1b3f7'
down_revision: Union[str, None] = 'c7a1d4f6e8b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('cash_sessions') as batch_op:
        batch_op.add_column(sa.Column('resolved_by', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('resolution_comment', sa.Text(), nullable=True))
        batch_op.create_foreign_key('fk_cash_sessions_resolved_by', 'users', ['resolved_by'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('cash_sessions') as batch_op:
        batch_op.drop_constraint('fk_cash_sessions_resolved_by', type_='foreignkey')
        batch_op.drop_column('resolution_comment')
        batch_op.drop_column('resolved_at')
        batch_op.drop_column('resolved_by')
