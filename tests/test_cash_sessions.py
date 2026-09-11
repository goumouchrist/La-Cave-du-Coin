import pytest

from app.models import CashSessionStatus, MovementType, PaymentMode, Product, Role
from app.services import cash as cash_service
from app.services import sales as sales_service
from app.services import stock as stock_service
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


def _setup_product_with_stock(db_session, admin, manager, qty_units=100, prix_vente=5000, prix_achat=3000):
    product = Product(
        name="Coca-Cola 33cl", category="Sodas", barcode="1234567890123",
        unit_carton_qty=24, unit_pack_qty=6, prix_achat=prix_achat, prix_vente=prix_vente, stock_min_cartons=5,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    movement = stock_service.create_movement(db_session, product, MovementType.ENTREE, qty=qty_units, unit="unite", created_by=admin.id)
    stock_service.validate_movement(db_session, movement, manager, approve=True)
    return product


def test_summary_breaks_down_sales_by_payment_mode(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = _setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=10000)

    sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.ESPECES, amount_given=5000,
        items=[{"product_id": product.id, "qty": 1}],
    )
    sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.PAYCARD, amount_given=5000,
        items=[{"product_id": product.id, "qty": 1}],
    )

    summary = cash_service.compute_summary(db_session, session_)

    assert summary["by_payment_mode"] == {"especes": 5000, "paycard": 5000}
    assert summary["theoretical_cash"] == 10000 + 5000  # seules les Espèces comptent
    assert summary["sales_count"] == 2
    assert summary["opening_amount"] == 10000


def test_summary_excludes_cancelled_sales(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = _setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)

    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.ESPECES, amount_given=5000,
        items=[{"product_id": product.id, "qty": 1}],
    )
    sales_service.cancel_sale(db_session, sale, manager, reason="Erreur de saisie")

    summary = cash_service.compute_summary(db_session, session_)
    assert summary["by_payment_mode"] == {}
    assert summary["sales_count"] == 0


def test_list_sessions_endpoint_returns_history_most_recent_first(client, auth_headers):
    headers = auth_headers("cashier2", Role.CAISSIER)

    first = client.post("/api/cash-sessions/open", json={"opening_amount": 1000}, headers=headers).json()
    client.post(f"/api/cash-sessions/{first['id']}/close", json={"closing_physical": 1000}, headers=headers)
    second = client.post("/api/cash-sessions/open", json={"opening_amount": 2000}, headers=headers).json()

    res = client.get("/api/cash-sessions", headers=headers)
    assert res.status_code == 200
    sessions = res.json()
    assert [s["id"] for s in sessions[:2]] == [second["id"], first["id"]]


def test_summary_endpoint_reflects_open_session_sales(client, auth_headers):
    admin_headers = auth_headers("admin2", Role.ADMIN)
    manager_headers = auth_headers("manager2", Role.MANAGER)
    cashier_headers = auth_headers("cashier3", Role.CAISSIER)

    product = client.post(
        "/api/products",
        json={
            "name": "Fanta 33cl", "category": "Sodas", "prix_achat": 3000, "prix_vente": 5000,
        },
        headers=admin_headers,
    ).json()
    movement = client.post(
        "/api/stock/movements",
        json={"product_id": product["id"], "type": "entree", "qty": 10, "unit": "unite"},
        headers=admin_headers,
    ).json()
    client.post(f"/api/stock/movements/{movement['id']}/validate", json={"approve": True}, headers=manager_headers)

    session_ = client.post("/api/cash-sessions/open", json={"opening_amount": 0}, headers=cashier_headers).json()
    client.post(
        "/api/sales",
        json={
            "cash_session_id": session_["id"], "payment_mode": "especes", "amount_given": 5000,
            "items": [{"product_id": product["id"], "qty": 1}],
        },
        headers=cashier_headers,
    )

    res = client.get(f"/api/cash-sessions/{session_['id']}/summary", headers=cashier_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["by_payment_mode"] == {"especes": 5000}
    assert body["theoretical_cash"] == 5000
    assert body["sales_count"] == 1


def test_resolve_blocked_session_closes_it_with_comment(db_session):
    cashier = create_user(db_session, "cashier4", "pw", Role.CAISSIER)
    manager = create_user(db_session, "manager3", "pw", Role.MANAGER)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=50000)
    blocked = cash_service.close_session(db_session, session_, cashier.id, closing_physical=65000)
    assert blocked.status == CashSessionStatus.BLOCKED

    resolved = cash_service.resolve_blocked_session(
        db_session, blocked, manager.id, "Erreur de comptage vérifiée avec le caissier, écart justifié."
    )

    assert resolved.status == CashSessionStatus.CLOSED
    assert resolved.resolved_by == manager.id
    assert resolved.resolution_comment == "Erreur de comptage vérifiée avec le caissier, écart justifié."
    assert resolved.resolved_at is not None


def test_cannot_resolve_a_session_that_is_not_blocked(db_session):
    cashier = create_user(db_session, "cashier5", "pw", Role.CAISSIER)
    manager = create_user(db_session, "manager4", "pw", Role.MANAGER)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=50000)
    closed = cash_service.close_session(db_session, session_, cashier.id, closing_physical=50000)

    with pytest.raises(cash_service.SessionNotBlockedError):
        cash_service.resolve_blocked_session(db_session, closed, manager.id, "peu importe")


def test_resolve_endpoint_requires_manager_role_and_logs_action(db_session, client, auth_headers):
    cashier_headers = auth_headers("cashier6", Role.CAISSIER)
    manager_headers = auth_headers("manager5", Role.MANAGER)

    opened = client.post("/api/cash-sessions/open", json={"opening_amount": 50000}, headers=cashier_headers).json()
    blocked = client.post(
        f"/api/cash-sessions/{opened['id']}/close", json={"closing_physical": 65000}, headers=cashier_headers
    ).json()
    assert blocked["status"] == "blocked"

    forbidden = client.post(
        f"/api/cash-sessions/{opened['id']}/resolve", json={"comment": "peu importe"}, headers=cashier_headers
    )
    assert forbidden.status_code == 403

    res = client.post(
        f"/api/cash-sessions/{opened['id']}/resolve",
        json={"comment": "Vérifié avec le caissier, écart accepté."},
        headers=manager_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "closed"
    assert body["resolution_comment"] == "Vérifié avec le caissier, écart accepté."

    from app.models import Log
    log = db_session.query(Log).filter(Log.action == "cash_session_resolved").first()
    assert log is not None
