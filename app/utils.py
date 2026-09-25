import uuid
from datetime import datetime, timezone

from app.config import settings


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


def _generate_reference(prefix: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{ts}-{uuid.uuid4().hex[:6].upper()}"


def generate_transaction_number() -> str:
    return _generate_reference("TX")


def generate_quote_number() -> str:
    return _generate_reference("DEV")
