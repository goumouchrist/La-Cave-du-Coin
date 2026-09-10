import pytest

from app.models import MovementType, PaymentMode, Product, Role, SaleStatus
from app.services import cash as cash_service
from app.services import products as products_service
from app.services import receipts as receipts_service
from app.services import sales as sales_service
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


def test_create_sale_decrements_stock_and_computes_change(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)

    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=20000)

    sale = sales_service.create_sale(
        db_session,
        cashier,
        session_.id,
        PaymentMode.ESPECES,
        amount_given=11000,
        items=[{"product_id": product.id, "qty": 2, "quantity_confirmed": False}],
    )

    assert sale.total_amount == 10000
    assert sale.change_amount == 1000
    assert products_service.get_current_stock_units(db_session, product.id) == 98


def test_sale_blocked_when_cash_session_not_open(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)

    with pytest.raises(sales_service.CashSessionClosedError):
        sales_service.create_sale(
            db_session, cashier, 999, PaymentMode.ESPECES, amount_given=5000,
            items=[{"product_id": product.id, "qty": 1}],
        )


def test_sale_blocked_when_insufficient_stock(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager, qty_units=1)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)

    with pytest.raises(sales_service.InsufficientStockError):
        sales_service.create_sale(
            db_session, cashier, session_.id, PaymentMode.ESPECES, amount_given=50000,
            items=[{"product_id": product.id, "qty": 5}],
        )


def test_more_than_five_identical_items_requires_confirmation(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)

    with pytest.raises(sales_service.QuantityConfirmationRequiredError):
        sales_service.create_sale(
            db_session, cashier, session_.id, PaymentMode.ESPECES, amount_given=50000,
            items=[{"product_id": product.id, "qty": 6, "quantity_confirmed": False}],
        )

    # Avec confirmation explicite, la vente passe
    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.ESPECES, amount_given=50000,
        items=[{"product_id": product.id, "qty": 6, "quantity_confirmed": True}],
    )
    assert sale.total_amount == 6 * product.prix_vente


def test_manager_can_cancel_sale_anytime(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.ESPECES, amount_given=5000,
        items=[{"product_id": product.id, "qty": 1}],
    )

    cancelled = sales_service.cancel_sale(db_session, sale, manager, reason="Erreur de saisie")
    assert cancelled.status == SaleStatus.ANNULEE


def test_cashier_cannot_cancel_without_reason(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.ESPECES, amount_given=5000,
        items=[{"product_id": product.id, "qty": 1}],
    )

    with pytest.raises(sales_service.CancelNotAllowedError):
        sales_service.cancel_sale(db_session, sale, cashier, reason="")


def test_second_print_is_marked_as_duplicata(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.ESPECES, amount_given=5000,
        items=[{"product_id": product.id, "qty": 1}],
    )

    assert sales_service.register_print(db_session, sale) is False
    assert sales_service.register_print(db_session, sale) is True


def test_receipt_pdf_is_generated(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.ESPECES, amount_given=5000,
        items=[{"product_id": product.id, "qty": 1}],
    )

    pdf_bytes = receipts_service.build_receipt_pdf(sale, {product.id: product}, "Caissier Test", is_duplicata=False)
    assert pdf_bytes[:4] == b"%PDF"


def test_receipt_pdf_with_tva_is_generated(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    product.tva_rate = 0.18
    db_session.commit()

    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.ESPECES, amount_given=5000,
        items=[{"product_id": product.id, "qty": 1}],
    )

    assert receipts_service.compute_total_tva(sale, {product.id: product}) == round(product.prix_vente * 0.18)

    pdf_bytes = receipts_service.build_receipt_pdf(sale, {product.id: product}, "Caissier Test", is_duplicata=False)
    assert pdf_bytes[:4] == b"%PDF"
