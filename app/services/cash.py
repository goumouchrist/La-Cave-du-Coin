from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import CashSession, CashSessionStatus, PaymentMode, Return, Sale, SaleStatus


class SessionAlreadyOpenError(Exception):
    pass


class SessionNotOpenError(Exception):
    pass


class SessionNotBlockedError(Exception):
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
    cash_refunds = db.query(func.coalesce(func.sum(Return.total_refund_gnf), 0)).filter(
        Return.cash_session_id == session_.id,
        Return.refund_mode == PaymentMode.ESPECES,
    ).scalar()
    return session_.opening_amount + int(cash_sales) - int(cash_refunds)


def resolve_blocked_session(db: Session, session_: CashSession, resolver_id: int, comment: str) -> CashSession:
    """Un Manager/Admin examine une session bloquée (écart trop important) et
    la clôture réellement une fois l'écart expliqué/vérifié, en laissant une
    trace (qui, quand, pourquoi) plutôt que de la laisser indéfiniment
    "blocked" sans suite possible."""
    if session_.status != CashSessionStatus.BLOCKED:
        raise SessionNotBlockedError("Cette session n'est pas bloquée")

    session_.status = CashSessionStatus.CLOSED
    session_.resolved_by = resolver_id
    session_.resolved_at = datetime.now(timezone.utc)
    session_.resolution_comment = comment
    db.commit()
    db.refresh(session_)
    return session_


def compute_summary(db: Session, session_: CashSession) -> dict:
    """Répartition des ventes de la session par mode de paiement, pour aider
    au comptage avant la fermeture : seul le montant en Espèces (théorique)
    doit se retrouver physiquement dans le tiroir, les autres modes
    (Mobile Money, Paycard, Crédit...) ne mettent pas d'argent liquide en
    caisse mais sont utiles à afficher pour vérifier le total des ventes."""
    rows = (
        db.query(Sale.payment_mode, func.sum(Sale.total_amount), func.count(Sale.id))
        .filter(Sale.cash_session_id == session_.id, Sale.status == SaleStatus.VALIDE)
        .group_by(Sale.payment_mode)
        .all()
    )
    by_payment_mode = {mode.value: int(total) for mode, total, _ in rows}
    sales_count = sum(count for _, _, count in rows)
    return {
        "session_id": session_.id,
        "opening_amount": session_.opening_amount,
        "theoretical_cash": compute_theoretical_amount(db, session_),
        "by_payment_mode": by_payment_mode,
        "sales_count": sales_count,
    }


def list_cash_movements(db: Session, session_: CashSession) -> list[dict]:
    """Détail chronologique de tout ce qui compose le montant théorique en
    espèces de la session (ventes espèces + remboursements espèces, avec un
    total qui s'accumule au fil du temps) : permet au caissier de vérifier en
    cours de journée que le tiroir correspond bien à ce qu'attend le système,
    plutôt que de découvrir un écart uniquement au moment de la fermeture."""
    sales = (
        db.query(Sale)
        .filter(
            Sale.cash_session_id == session_.id,
            Sale.payment_mode == PaymentMode.ESPECES,
            Sale.status == SaleStatus.VALIDE,
        )
        .all()
    )
    refunds = (
        db.query(Return)
        .filter(Return.cash_session_id == session_.id, Return.refund_mode == PaymentMode.ESPECES)
        .all()
    )

    entries = [
        {
            "movement_type": "vente",
            "sale_id": sale.id,
            "transaction_number": sale.transaction_number,
            "cashier_id": sale.cashier_id,
            "amount": sale.total_amount,
            "created_at": sale.created_at,
        }
        for sale in sales
    ] + [
        {
            "movement_type": "remboursement_especes",
            "return_id": refund.id,
            "cashier_id": refund.processed_by,
            "amount": -refund.total_refund_gnf,
            "created_at": refund.created_at,
        }
        for refund in refunds
    ]
    entries.sort(key=lambda e: e["created_at"])

    running_total = session_.opening_amount
    movements = []
    for entry in entries:
        running_total += entry["amount"]
        movements.append({**entry, "running_total": running_total})
    return movements


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
