import json

from sqlalchemy.orm import Session

from app.models import Log


def record(db: Session, user_id: int | None, action: str, details: dict | None = None, ip_address: str | None = None) -> Log:
    log = Log(
        user_id=user_id,
        action=action,
        details=json.dumps(details, default=str) if details else None,
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
