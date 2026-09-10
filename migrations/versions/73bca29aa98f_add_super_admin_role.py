"""add super admin role

Revision ID: 73bca29aa98f
Revises: 5990ccfd5856
Create Date: 2026-09-10 17:17:43.211042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '73bca29aa98f'
down_revision: Union[str, None] = '5990ccfd5856'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite stocke le rôle en simple VARCHAR sans contrainte de longueur
    # réellement appliquée (rien à faire). PostgreSQL utilise un vrai type
    # ENUM natif : il faut y ajouter explicitement la nouvelle valeur.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE role ADD VALUE IF NOT EXISTS 'super_admin'")


def downgrade() -> None:
    # PostgreSQL ne permet pas de retirer une valeur d'un type ENUM existant
    # sans le recréer entièrement — non géré ici (downgrade non destructif).
    pass
