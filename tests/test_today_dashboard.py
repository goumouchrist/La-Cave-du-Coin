from app.models import MovementType, Product, Role
from app.services import stock as stock_service
from app.services.users import create_user


def setup_product_with_stock(db_session, admin, manager, qty_units=100, prix_vente=5000, prix_achat=3000):
    product = Product(
        name="Coca-Cola 33cl",
        category="Sodas",
        barcode="1234567890123",
        unit_carton_qty=24,
        unit_pack_qty=6,
        prix_achat=prix_achat,
        prix_vente=prix_vente,
        stock_min_cartons=5,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    movement = stock_service.create_movement(db_session, product, MovementType.ENTREE, qty=qty_units, unit="unite", created_by=admin.id)
    stock_service.validate_movement(db_session, movement, manager, approve=True)
    return product


def test_today_summary_and_activity_reflect_todays_movements(client, auth_headers, db_session):
    headers = auth_headers("manager", Role.MANAGER)
    admin = create_user(db_session, "admin", "pw2", Role.ADMIN)
    manager2 = create_user(db_session, "manager2", "pw2", Role.MANAGER)
    product = setup_product_with_stock(db_session, admin, manager2)

    open_res = client.post("/api/cash-sessions/open", json={"opening_amount": 0}, headers=headers)
    assert open_res.status_code == 201, open_res.text
    session_id = open_res.json()["id"]

    sale_res = client.post(
        "/api/sales",
        json={
            "cash_session_id": session_id,
            "payment_mode": "especes",
            "amount_given": 5000,
            "items": [{"product_id": product.id, "qty": 1}],
        },
        headers=headers,
    )
    assert sale_res.status_code == 201, sale_res.text

    quote_res = client.post(
        "/api/quotes",
        json={"items": [{"product_id": product.id, "qty": 1}], "customer_name": "Client Test", "customer_phone": "600000000"},
        headers=headers,
    )
    assert quote_res.status_code == 201, quote_res.text
    quote_id = quote_res.json()["id"]

    convert_res = client.post(
        f"/api/quotes/{quote_id}/convert",
        json={"cash_session_id": session_id, "payment_mode": "especes", "amount_given": 5000},
        headers=headers,
    )
    assert convert_res.status_code == 201, convert_res.text

    close_res = client.post(f"/api/cash-sessions/{session_id}/close", json={"closing_physical": 999999}, headers=headers)
    assert close_res.status_code == 200, close_res.text
    assert close_res.json()["status"] == "blocked"

    summary_res = client.get("/api/stats/today-summary", headers=headers)
    assert summary_res.status_code == 200, summary_res.text
    summary = summary_res.json()
    assert summary["sales_count"] == 2
    assert summary["revenue_gnf"] == 10000
    assert summary["quotes_created_count"] == 1
    assert summary["quotes_converted_count"] == 1
    assert summary["stock_movements_count"] >= 1
    assert summary["cash_gap_alerts_count"] == 1

    activity_res = client.get("/api/stats/today-activity", headers=headers)
    assert activity_res.status_code == 200, activity_res.text
    actions = [item["action"] for item in activity_res.json()]
    for expected in ["cash_session_opened", "sale_created", "quote_created", "quote_converted", "cash_session_blocked"]:
        assert expected in actions

    products_res = client.get("/api/stats/today-products", headers=headers)
    assert products_res.status_code == 200, products_res.text
    products = products_res.json()
    assert len(products) == 1
    assert products[0]["name"] == product.name
    assert products[0]["qty_sold"] == 2  # la vente directe + la conversion du devis, 1 unité chacune


def test_today_products_empty_when_no_sales(client, auth_headers):
    headers = auth_headers("manager", Role.MANAGER)
    res = client.get("/api/stats/today-products", headers=headers)
    assert res.status_code == 200
    assert res.json() == []


def test_today_activity_excludes_non_movement_actions(client, auth_headers, db_session):
    headers = auth_headers("manager", Role.MANAGER)

    activity_res = client.get("/api/stats/today-activity", headers=headers)
    assert activity_res.status_code == 200
    actions = [item["action"] for item in activity_res.json()]
    assert "login_success" not in actions


def test_today_stats_forbidden_for_caissier(client, auth_headers):
    headers = auth_headers("cashier", Role.CAISSIER)
    res = client.get("/api/stats/today-summary", headers=headers)
    assert res.status_code == 403
