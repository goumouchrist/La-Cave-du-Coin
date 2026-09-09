from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Product, ScanLog


def log_scan(db: Session, user_id: int, product: Product, action_type: str) -> tuple[ScanLog, bool]:
    """Enregistre un scan et détecte un double scan du même produit en < DOUBLE_SCAN_WINDOW_SECONDS."""
    window_start = datetime.now(timezone.utc) - timedelta(seconds=settings.DOUBLE_SCAN_WINDOW_SECONDS)
    recent = (
        db.query(ScanLog)
        .filter(
            ScanLog.product_id == product.id,
            ScanLog.user_id == user_id,
            ScanLog.created_at >= window_start,
        )
        .order_by(ScanLog.created_at.desc())
        .first()
    )
    is_double_scan = recent is not None

    scan_log = ScanLog(user_id=user_id, product_id=product.id, action_type=action_type)
    db.add(scan_log)
    db.commit()
    db.refresh(scan_log)
    return scan_log, is_double_scan
