import pytest

from app.models import CashSessionStatus, Role
from app.services import cash as cash_service
from app.services.users import create_user


def test_open_session_success(db_session):
    user = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    session_ = cash_service.open_session(db_session, user.id, opening_amount=50000)
    assert session_.status == CashSessionStatus.OPEN
    assert session_.opening_amount == 50000


def test_cannot_open_two_sessions_at_once(db_session):
    user = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    cash_service.open_session(db_session, user.id, opening_amount=50000)
    with pytest.raises(cash_service.SessionAlreadyOpenError):
        cash_service.open_session(db_session, user.id, opening_amount=10000)


def test_close_session_within_threshold_is_closed(db_session):
    user = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    session_ = cash_service.open_session(db_session, user.id, opening_amount=50000)

    closed = cash_service.close_session(db_session, session_, user.id, closing_physical=50000)
    assert closed.status == CashSessionStatus.CLOSED
    assert closed.gap_amount == 0
    assert closed.closing_theoretical == 50000


def test_close_session_with_large_gap_is_blocked(db_session):
    user = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    session_ = cash_service.open_session(db_session, user.id, opening_amount=50000)

    # Écart de 15 000 GNF > seuil par défaut de 10 000 GNF
    closed = cash_service.close_session(db_session, session_, user.id, closing_physical=65000)
    assert closed.status == CashSessionStatus.BLOCKED
    assert closed.gap_amount == 15000


def test_cannot_close_already_closed_session(db_session):
    user = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    session_ = cash_service.open_session(db_session, user.id, opening_amount=50000)
    cash_service.close_session(db_session, session_, user.id, closing_physical=50000)

    with pytest.raises(cash_service.SessionNotOpenError):
        cash_service.close_session(db_session, session_, user.id, closing_physical=50000)
