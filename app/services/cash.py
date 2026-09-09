from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import CashSession, CashSessionStatus, PaymentMode, Sale, SaleStatus


class SessionAlreadyOpenError(Exception):
    pass


class SessionNotOpenError(Exception):
    pass


def open_session(db: Session, user_id: int, opening_amount: int) -> CashSession:
    existing = db.query(CashSession).filter(CashSession.status == CashSessionStatus.OPEN).first()
    if existing:
        raise SessionAlreadyOpenError("Une session de caisse est déjà ouverte")

    session_ = CashSession(opened_by=user_id, opening_amount=opening_amount, status=CashSessionStatus.OPEN)
    db.add(session_)
    db.commit()
    db.refresh(session_)
    return session_


def compute_theoretical_amount(db: Session, session_: CashSession) -> int:
    cash_sales = db.query(func.coalesce(func.sum(Sale.total_amount), 0)).filter(
        Sale.cash_session_id == session_.id,
        Sale.payment_mode == PaymentMode.ESPECES,
        Sale.status == SaleStatus.VALIDE,
    ).scalar()
    return session_.opening_amount + int(cash_sales)


def close_session(db: Session, session_: CashSession, user_id: int, closing_physical: int) -> CashSession:
    if session_.status != CashSessionStatus.OPEN:
        raise SessionNotOpenError("Cette session de caisse n'est pas ouverte")

    theoretical = compute_theoretical_amount(db, session_)
    gap = closing_physical - theoretical

    session_.closing_theoretical = theoretical
    session_.closing_physical = closing_physical
    session_.gap_amount = gap
    session_.closed_by = user_id
    session_.closed_at = datetime.now(timezone.utc)

    if abs(gap) > settings.CASH_GAP_ALERT_THRESHOLD_GNF:
        session_.status = CashSessionStatus.BLOCKED
    else:
        session_.status = CashSessionStatus.CLOSED

    db.commit()
    db.refresh(session_)
    return session_
