import secrets
from datetime import datetime, timezone

from app.config import settings

# Sans 0/O, 1/I/L : évite les confusions à la relecture d'un numéro imprimé
# ou tapé au clavier.
_SHORT_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def to_aware_utc(dt: datetime) -> datetime:
    """SQLite ne conserve pas le fuseau horaire : les datetimes relus depuis la base
    sont naïfs bien que toujours stockés en UTC. On les rend explicitement UTC pour
    pouvoir les comparer à datetime.now(timezone.utc)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def round_gnf(amount: int) -> int:
    """Arrondit un montant GNF au multiple de ROUNDING_STEP_GNF le plus proche (pas de centimes)."""
    step = settings.ROUNDING_STEP_GNF
    if step <= 1:
        return amount
    return int(round(amount / step) * step)


def generate_short_code(length: int = 5) -> str:
    """Code court aléatoire (numéro de vente/devis) : facile à taper au clavier,
    à lire sur un reçu papier, ou à scanner via le QR code imprimé."""
    return "".join(secrets.choice(_SHORT_CODE_ALPHABET) for _ in range(length))
