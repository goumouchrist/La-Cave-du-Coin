"""fix enum label casing for postgresql

Revision ID: e26325b85a44
Revises: 73bca29aa98f
Create Date: 2026-09-10 17:32:05.715603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e26325b85a44'
down_revision: Union[str, None] = '73bca29aa98f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Corrige une erreur des deux migrations précédentes (5990ccfd5856,
    # 73bca29aa98f) : SQLAlchemy stocke le NOM du membre d'énumération
    # Python (ex. "SUPER_ADMIN"), pas sa valeur (ex. "super_admin"), pour un
    # type ENUM natif PostgreSQL. Ces migrations avaient ajouté les valeurs en
    # minuscule (inutilisées, sans risque de les laisser) au lieu des noms en
    # majuscule réellement utilisés par l'application. Idempotent (IF NOT
    # EXISTS) : sans effet sur une base qui n'a pas encore ce défaut (ex.
    # nouvelle installation qui a déjà les bons noms via les migrations
    # corrigées).
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for value in ["SOUTRA_MONEY", "CREDIT_MONEY", "PAYCARD"]:
        op.execute(f"ALTER TYPE paymentmode ADD VALUE IF NOT EXISTS '{value}'")

    op.execute("ALTER TYPE role ADD VALUE IF NOT EXISTS 'SUPER_ADMIN'")


def downgrade() -> None:
    pass
