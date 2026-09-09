import pytest

from app.models import MovementType, PaymentMode, Product, Role
from app.services import cash as cash_service
from app.services import customers as customers_service
from app.services import returns as returns_service
from app.services import sales as sales_service
from app.services import stock as stock_service
from app.services.users import create_user


def setup_product_with_stock(db_session, admin, manager, qty_units=100, prix_vente=5000, prix_achat=3000):
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


def make_sale(db_session, cashier, session_, product, qty=2):
    return sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.ESPECES, amount_given=product.prix_vente * qty,
        items=[{"product_id": product.id, "qty": qty}],
    )


def test_return_credits_customer_and_restores_stock(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    sale = make_sale(db_session, cashier, session_, product, qty=2)

    stock_before_return = 100 - 2

    return_ = returns_service.create_return(
        db_session, sale,
        items=[{"sale_item_id": sale.items[0].id, "qty": 1}],
        customer_name="Fatou Camara", customer_phone="+224600000001",
        processed_by=cashier, reason="Bouteille défectueuse",
    )

    assert return_.total_refund_gnf == product.prix_vente

    from app.services.products import get_current_stock_units
    assert get_current_stock_units(db_session, product.id) == stock_before_return + 1

    from app.models import Customer
    customer = db_session.get(Customer, return_.customer_id)
    assert customer.credit_balance_gnf == product.prix_vente


def test_cannot_return_more_than_sold_quantity(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    sale = make_sale(db_session, cashier, session_, product, qty=2)

    with pytest.raises(returns_service.ReturnQuantityExceededError):
        returns_service.create_return(
            db_session, sale,
            items=[{"sale_item_id": sale.items[0].id, "qty": 3}],
            customer_name="Fatou Camara", customer_phone="+224600000001",
            processed_by=cashier,
        )


def test_cannot_return_the_same_line_twice_beyond_sold_quantity(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    sale = make_sale(db_session, cashier, session_, product, qty=2)

    returns_service.create_return(
        db_session, sale, items=[{"sale_item_id": sale.items[0].id, "qty": 1}],
        customer_name="Fatou Camara", customer_phone="+224600000001", processed_by=cashier,
    )

    with pytest.raises(returns_service.ReturnQuantityExceededError):
        returns_service.create_return(
            db_session, sale, items=[{"sale_item_id": sale.items[0].id, "qty": 2}],
            customer_name="Fatou Camara", customer_phone="+224600000001", processed_by=cashier,
        )


def test_returning_same_phone_reuses_existing_customer_and_accumulates_credit(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)

    sale1 = make_sale(db_session, cashier, session_, product, qty=2)
    return1 = returns_service.create_return(
        db_session, sale1, items=[{"sale_item_id": sale1.items[0].id, "qty": 1}],
        customer_name="Fatou Camara", customer_phone="+224600000001", processed_by=cashier,
    )

    sale2 = make_sale(db_session, cashier, session_, product, qty=1)
    return2 = returns_service.create_return(
        db_session, sale2, items=[{"sale_item_id": sale2.items[0].id, "qty": 1}],
        customer_name="Fatou Camara", customer_phone="+224600000001", processed_by=cashier,
    )

    assert return1.customer_id == return2.customer_id
    from app.models import Customer
    customer = db_session.get(Customer, return1.customer_id)
    assert customer.credit_balance_gnf == 2 * product.prix_vente


def test_sale_with_avoir_debits_customer_credit(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)

    customer = customers_service.find_or_create_customer(db_session, "Fatou Camara", "+224600000001")
    customers_service.credit_account(db_session, customer, 20000)

    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.AVOIR, amount_given=0,
        items=[{"product_id": product.id, "qty": 2}],
        customer_id=customer.id,
    )

    assert sale.total_amount == 2 * product.prix_vente
    assert sale.change_amount == 0

    db_session.refresh(customer)
    assert customer.credit_balance_gnf == 20000 - 2 * product.prix_vente


def test_sale_with_avoir_requires_customer_id(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)

    with pytest.raises(sales_service.CustomerRequiredError):
        sales_service.create_sale(
            db_session, cashier, session_.id, PaymentMode.AVOIR, amount_given=0,
            items=[{"product_id": product.id, "qty": 1}],
        )


def test_sale_with_avoir_blocked_when_credit_insufficient(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)

    customer = customers_service.find_or_create_customer(db_session, "Fatou Camara", "+224600000001")
    customers_service.credit_account(db_session, customer, 1000)

    with pytest.raises(customers_service.InsufficientCreditError):
        sales_service.create_sale(
            db_session, cashier, session_.id, PaymentMode.AVOIR, amount_given=0,
            items=[{"product_id": product.id, "qty": 1}],
            customer_id=customer.id,
        )
