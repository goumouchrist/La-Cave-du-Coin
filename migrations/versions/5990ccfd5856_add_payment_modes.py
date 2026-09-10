"""add payment modes

Revision ID: 5990ccfd5856
Revises: 9ab15f641c93
Create Date: 2026-09-10 15:46:02.637870

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5990ccfd5856'
down_revision: Union[str, None] = '9ab15f641c93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_VALUES = ["SOUTRA_MONEY", "CREDIT_MONEY", "PAYCARD"]  # SQLAlchemy stocke le NOM du membre, pas sa valeur


def upgrade() -> None:
    # SQLite stocke l'enum en simple VARCHAR sans contrainte CHECK ici (rien à
    # faire). PostgreSQL utilise un vrai type ENUM natif : il faut y ajouter
    # explicitement chaque nouvelle valeur (ALTER TYPE ... ADD VALUE, impossible
    # à batcher, une commande par valeur).
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for value in NEW_VALUES:
            op.execute(f"ALTER TYPE paymentmode ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # PostgreSQL ne permet pas de retirer une valeur d'un type ENUM existant
    # sans le recréer entièrement — non géré ici (downgrade non destructif).
    pass
