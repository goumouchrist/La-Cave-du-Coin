from datetime import datetime, timedelta, timezone

import pytest

from app.models import MovementType, PaymentMode, Product, Role
from app.services import cash as cash_service
from app.services import sales as sales_service
from app.services import scan as scan_service
from app.services import stock as stock_service
from app.services.users import create_user


def setup_product_with_stock(db_session, admin, manager, qty_units=100):
    product = Product(
        name="Coca-Cola 33cl", category="Sodas", barcode="1234567890123",
        unit_carton_qty=24, unit_pack_qty=6, prix_achat=3000, prix_vente=5000, stock_min_cartons=5,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    movement = stock_service.create_movement(db_session, product, MovementType.ENTREE, qty=qty_units, unit="unite", created_by=admin.id)
    stock_service.validate_movement(db_session, movement, manager, approve=True)
    return product


def test_cashier_cannot_cancel_after_five_minutes(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.ESPECES, amount_given=5000,
        items=[{"product_id": product.id, "qty": 1}],
    )

    sale.created_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db_session.commit()

    with pytest.raises(sales_service.CancelNotAllowedError):
        sales_service.cancel_sale(db_session, sale, cashier, reason="Trop tard")


def test_cashier_can_cancel_within_five_minutes_with_reason(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.ESPECES, amount_given=5000,
        items=[{"product_id": product.id, "qty": 1}],
    )

    cancelled = sales_service.cancel_sale(db_session, sale, cashier, reason="Erreur produit scanné")
    assert cancelled.status.value == "annulee"


def test_cannot_cancel_twice(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.ESPECES, amount_given=5000,
        items=[{"product_id": product.id, "qty": 1}],
    )
    sales_service.cancel_sale(db_session, sale, manager, reason="Premier motif")

    with pytest.raises(sales_service.AlreadyCancelledError):
        sales_service.cancel_sale(db_session, sale, manager, reason="Deuxième motif")


def test_double_scan_within_window_is_detected(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    product = setup_product_with_stock(db_session, admin, manager)

    _, first_is_double = scan_service.log_scan(db_session, admin.id, product, "vente")
    _, second_is_double = scan_service.log_scan(db_session, admin.id, product, "vente")

    assert first_is_double is False
    assert second_is_double is True


def test_scan_outside_window_is_not_flagged_as_double(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    product = setup_product_with_stock(db_session, admin, manager)

    from app.models import ScanLog

    scan_service.log_scan(db_session, admin.id, product, "vente")
    old_scan = db_session.query(ScanLog).first()
    old_scan.created_at = datetime.now(timezone.utc) - timedelta(seconds=30)
    db_session.commit()

    _, is_double = scan_service.log_scan(db_session, admin.id, product, "vente")
    assert is_double is False
