from datetime import date, datetime, timedelta, timezone

from app.models import (
    MovementStatus,
    MovementType,
    PaymentMode,
    Product,
    Role,
    Sale,
    SaleItem,
    SaleStatus,
    StockMovement,
)
from app.services import cash as cash_service
from app.services import predictions as predictions_service
from app.services.users import create_user


def make_product(db_session, name="Coca-Cola 33cl", **overrides):
    data = dict(name=name, category="Sodas", prix_achat=3000, prix_vente=5000, unit_carton_qty=24, unit_pack_qty=6, stock_min_cartons=5)
    data.update(overrides)
    product = Product(**data)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def make_sale_with_date(db_session, cash_session_id, cashier_id, product, qty, days_ago):
    created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    sale = Sale(
        transaction_number=f"TX-TEST-{days_ago}-{product.id}-{qty}",
        cash_session_id=cash_session_id,
        cashier_id=cashier_id,
        payment_mode=PaymentMode.ESPECES,
        total_amount=product.prix_vente * qty,
        amount_given=product.prix_vente * qty,
        change_amount=0,
        status=SaleStatus.VALIDE,
        created_at=created_at,
    )
    sale.items = [SaleItem(product_id=product.id, qty_units=qty, unit_price=product.prix_vente, quantity_confirmed=False)]
    db_session.add(sale)
    db_session.commit()

    movement = StockMovement(
        product_id=product.id,
        type=MovementType.SORTIE_VENTE,
        qty_units=qty,
        status=MovementStatus.VALIDATED,
        created_by=cashier_id,
        validated_by=cashier_id,
        created_at=created_at,
    )
    db_session.add(movement)
    db_session.commit()
    return sale


def test_linear_regression_perfect_line():
    slope, intercept = predictions_service._linear_regression([0, 1, 2, 3], [10, 20, 30, 40])
    assert slope == 10
    assert intercept == 10


def test_linear_regression_constant_values():
    slope, intercept = predictions_service._linear_regression([0, 1, 2], [5, 5, 5])
    assert slope == 0
    assert intercept == 5


def test_top_selling_products_orders_by_quantity(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)

    coca = make_product(db_session, name="Coca-Cola", barcode="1111111111111")
    fanta = make_product(db_session, name="Fanta", barcode="2222222222222")

    make_sale_with_date(db_session, session_.id, cashier.id, coca, qty=10, days_ago=1)
    make_sale_with_date(db_session, session_.id, cashier.id, fanta, qty=3, days_ago=1)

    top = predictions_service.top_selling_products(db_session, days=7, limit=5)
    assert top[0]["name"] == "Coca-Cola"
    assert top[0]["qty_sold"] == 10
    assert top[1]["name"] == "Fanta"


def test_top_selling_products_excludes_old_sales(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    coca = make_product(db_session, name="Coca-Cola", barcode="1111111111111")

    make_sale_with_date(db_session, session_.id, cashier.id, coca, qty=10, days_ago=20)

    top = predictions_service.top_selling_products(db_session, days=7, limit=5)
    assert top == []


def test_stockout_forecast_computes_days_remaining(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)

    product = make_product(db_session, name="Coca-Cola", barcode="1111111111111")

    entree = StockMovement(
        product_id=product.id, type=MovementType.ENTREE, qty_units=300,
        status=MovementStatus.VALIDATED, created_by=admin.id, validated_by=manager.id,
    )
    db_session.add(entree)
    db_session.commit()

    # Consommation régulière : 10 unités/jour sur 10 jours => moyenne 30j = 100/30 ~= 3.33/jour
    for day in range(10):
        make_sale_with_date(db_session, session_.id, cashier.id, product, qty=10, days_ago=day)

    forecast = predictions_service.stockout_forecast(db_session, product, lookback_days=30)
    assert forecast["avg_daily_consumption"] == round(100 / 30, 2)
    remaining_stock = 300 - 100
    expected_days = round(remaining_stock / (100 / 30), 1)
    assert forecast["days_remaining"] == expected_days


def test_revenue_forecast_predicts_growth_trend(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    product = make_product(db_session, name="Coca-Cola", barcode="1111111111111")

    # CA croissant : 1, 2, 3 unités vendues il y a 2, 1, 0 jours (10000, 15000... GNF/jour croissants)
    make_sale_with_date(db_session, session_.id, cashier.id, product, qty=2, days_ago=2)
    make_sale_with_date(db_session, session_.id, cashier.id, product, qty=4, days_ago=1)
    make_sale_with_date(db_session, session_.id, cashier.id, product, qty=6, days_ago=0)

    forecast = predictions_service.forecast_next_day_revenue(db_session, history_days=30)
    assert forecast["based_on_days"] == 3
    assert forecast["predicted_revenue_gnf"] > 6 * product.prix_vente


def test_revenue_forecast_with_no_history_returns_zero(db_session):
    forecast = predictions_service.forecast_next_day_revenue(db_session, history_days=30)
    assert forecast == {"predicted_revenue_gnf": 0, "based_on_days": 0}


def test_expiring_batches_within_window(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    product = make_product(db_session, name="Yaourt", barcode="3333333333333")

    soon = date.today() + timedelta(days=3)
    far = date.today() + timedelta(days=60)

    db_session.add_all([
        StockMovement(
            product_id=product.id, type=MovementType.ENTREE, qty_units=20, expiry_date=soon,
            status=MovementStatus.VALIDATED, created_by=admin.id, validated_by=admin.id,
        ),
        StockMovement(
            product_id=product.id, type=MovementType.ENTREE, qty_units=20, expiry_date=far,
            status=MovementStatus.VALIDATED, created_by=admin.id, validated_by=admin.id,
        ),
    ])
    db_session.commit()

    alerts = predictions_service.expiring_batches(db_session, product, within_days=7)
    assert len(alerts) == 1
    assert alerts[0]["expiry_date"] == soon
    assert alerts[0]["remaining_units"] == 20
    assert alerts[0]["days_left"] == 3


def test_expiring_batches_excludes_depleted_batch(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    product = make_product(db_session, name="Yaourt", barcode="4444444444444")
    soon = date.today() + timedelta(days=2)

    db_session.add_all([
        StockMovement(
            product_id=product.id, type=MovementType.ENTREE, qty_units=10, expiry_date=soon,
            status=MovementStatus.VALIDATED, created_by=admin.id, validated_by=admin.id,
        ),
        StockMovement(
            product_id=product.id, type=MovementType.SORTIE_VENTE, qty_units=10,
            status=MovementStatus.VALIDATED, created_by=admin.id, validated_by=admin.id,
        ),
    ])
    db_session.commit()

    assert predictions_service.expiring_batches(db_session, product, within_days=7) == []


def test_expiry_alerts_endpoint_forbidden_for_caissier(client, auth_headers):
    headers = auth_headers("cashier", Role.CAISSIER)
    res = client.get("/api/stats/expiry-alerts", headers=headers)
    assert res.status_code == 403


def test_expiry_alerts_endpoint_returns_alerts_for_manager(client, auth_headers, db_session):
    headers = auth_headers("manager", Role.MANAGER)
    admin = create_user(db_session, "admin", "pw2", Role.ADMIN)
    product = make_product(db_session, name="Yaourt", barcode="5555555555555")
    soon = date.today() + timedelta(days=1)

    db_session.add(StockMovement(
        product_id=product.id, type=MovementType.ENTREE, qty_units=5, expiry_date=soon,
        status=MovementStatus.VALIDATED, created_by=admin.id, validated_by=admin.id,
    ))
    db_session.commit()

    res = client.get("/api/stats/expiry-alerts", headers=headers)
    assert res.status_code == 200, res.text
    alerts = res.json()
    assert any(a["product_id"] == product.id and a["remaining_units"] == 5 for a in alerts)
