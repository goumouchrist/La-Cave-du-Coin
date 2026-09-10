from datetime import date

import pytest

from app.models import MovementType, PaymentMode, Product, Role
from app.services import cash as cash_service
from app.services import customers as customers_service
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


def _setup(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    return admin, manager, cashier, product, session_


def test_credit_sale_with_partial_payment_records_debt(db_session):
    admin, manager, cashier, product, session_ = _setup(db_session)

    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.CREDIT, amount_given=3000,
        items=[{"product_id": product.id, "qty": 2}],
        customer_name="Fatou Camara", customer_phone="+224600000001", customer_address="Kaloum",
        due_date=date(2026, 10, 1),
    )

    assert sale.total_amount == 2 * product.prix_vente
    assert sale.remaining_due_gnf == sale.total_amount - 3000
    assert sale.due_date == date(2026, 10, 1)
    assert sale.customer_id is not None

    from app.models import Customer
    customer = db_session.get(Customer, sale.customer_id)
    assert customer.name == "Fatou Camara"
    assert customer.credit_balance_gnf == -(sale.total_amount - 3000)


def test_credit_sale_paid_in_full_records_no_debt(db_session):
    admin, manager, cashier, product, session_ = _setup(db_session)

    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.CREDIT, amount_given=product.prix_vente * 2,
        items=[{"product_id": product.id, "qty": 2}],
    )

    assert sale.remaining_due_gnf == 0
    assert sale.due_date is None
    assert sale.customer_id is None


def test_credit_sale_shortfall_without_customer_info_raises(db_session):
    admin, manager, cashier, product, session_ = _setup(db_session)

    with pytest.raises(sales_service.CustomerRequiredError):
        sales_service.create_sale(
            db_session, cashier, session_.id, PaymentMode.CREDIT, amount_given=1000,
            items=[{"product_id": product.id, "qty": 2}],
        )


def test_credit_sale_reuses_existing_customer_by_id(db_session):
    admin, manager, cashier, product, session_ = _setup(db_session)
    customer = customers_service.find_or_create_customer(db_session, "Fatou Camara", "+224600000001")

    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.CREDIT, amount_given=1000,
        items=[{"product_id": product.id, "qty": 2}],
        customer_id=customer.id,
    )

    assert sale.customer_id == customer.id
    db_session.refresh(customer)
    assert customer.credit_balance_gnf == -(sale.total_amount - 1000)


def test_list_customers_with_debt_returns_only_negative_balances(db_session):
    admin, manager, cashier, product, session_ = _setup(db_session)

    sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.CREDIT, amount_given=1000,
        items=[{"product_id": product.id, "qty": 2}],
        customer_name="Fatou Camara", customer_phone="+224600000001",
        due_date=date(2026, 10, 1),
    )
    customers_service.find_or_create_customer(db_session, "Client Sans Dette", "+224600000002")

    debts = customers_service.list_customers_with_debt(db_session)

    assert len(debts) == 1
    assert debts[0]["customer"].name == "Fatou Camara"
    assert debts[0]["amount_owed_gnf"] == product.prix_vente * 2 - 1000
    assert debts[0]["oldest_due_date"] == date(2026, 10, 1)


def test_repay_debt_reduces_balance(db_session):
    admin, manager, cashier, product, session_ = _setup(db_session)

    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.CREDIT, amount_given=1000,
        items=[{"product_id": product.id, "qty": 2}],
        customer_name="Fatou Camara", customer_phone="+224600000001",
    )

    from app.models import Customer
    customer = db_session.get(Customer, sale.customer_id)
    owed = sale.total_amount - 1000

    customers_service.credit_account(db_session, customer, owed)
    db_session.refresh(customer)
    assert customer.credit_balance_gnf == 0
    assert customers_service.list_customers_with_debt(db_session) == []


def test_record_repayment_persists_a_repayment_record(db_session):
    admin, manager, cashier, product, session_ = _setup(db_session)

    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.CREDIT, amount_given=1000,
        items=[{"product_id": product.id, "qty": 2}],
        customer_name="Fatou Camara", customer_phone="+224600000001",
    )

    from app.models import Customer
    customer = db_session.get(Customer, sale.customer_id)
    owed = sale.total_amount - 1000

    repayment = customers_service.record_repayment(db_session, customer, owed, processed_by=manager.id)

    assert repayment.id is not None
    assert repayment.amount_gnf == owed
    assert repayment.processed_by == manager.id
    assert repayment.customer.id == customer.id

    db_session.refresh(customer)
    assert customer.credit_balance_gnf == 0


def test_repay_debt_endpoint_logs_action_and_returns_receipt(db_session, client, auth_headers):
    _, manager, cashier, product, session_ = _setup(db_session)
    headers = auth_headers("apiadmin", Role.ADMIN)

    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.CREDIT, amount_given=1000,
        items=[{"product_id": product.id, "qty": 2}],
        customer_name="Fatou Camara", customer_phone="+224600000001",
    )
    owed = sale.total_amount - 1000

    res = client.post(f"/api/customers/{sale.customer_id}/repay-debt", json={"amount": owed}, headers=headers)
    assert res.status_code == 201, res.text
    repayment = res.json()
    assert repayment["amount_gnf"] == owed
    assert repayment["customer"]["credit_balance_gnf"] == 0

    from app.models import Log
    log = db_session.query(Log).filter(Log.action == "debt_repaid").first()
    assert log is not None

    pdf_res = client.get(f"/api/customers/repayments/{repayment['id']}/receipt.pdf", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.content[:4] == b"%PDF"


def test_third_unpaid_credit_sale_is_blocked_at_threshold(db_session):
    admin, manager, cashier, product, session_ = _setup(db_session)
    customer = customers_service.find_or_create_customer(db_session, "Fatou Camara", "+224600000001")

    for _ in range(2):
        sales_service.create_sale(
            db_session, cashier, session_.id, PaymentMode.CREDIT, amount_given=1000,
            items=[{"product_id": product.id, "qty": 1}],
            customer_id=customer.id,
        )

    with pytest.raises(sales_service.CreditLimitExceededError):
        sales_service.create_sale(
            db_session, cashier, session_.id, PaymentMode.CREDIT, amount_given=1000,
            items=[{"product_id": product.id, "qty": 1}],
            customer_id=customer.id,
        )


def test_credit_limit_resets_once_all_debts_are_repaid(db_session):
    admin, manager, cashier, product, session_ = _setup(db_session)
    customer = customers_service.find_or_create_customer(db_session, "Fatou Camara", "+224600000001")

    for _ in range(2):
        sales_service.create_sale(
            db_session, cashier, session_.id, PaymentMode.CREDIT, amount_given=1000,
            items=[{"product_id": product.id, "qty": 1}],
            customer_id=customer.id,
        )

    db_session.refresh(customer)
    owed = -customer.credit_balance_gnf
    customers_service.record_repayment(db_session, customer, owed, processed_by=manager.id)

    assert customers_service.count_active_credits(db_session, customer) == 0

    # Le compteur étant retombé à zéro, une nouvelle vente à crédit repasse.
    sale = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.CREDIT, amount_given=1000,
        items=[{"product_id": product.id, "qty": 1}],
        customer_id=customer.id,
    )
    assert sale.remaining_due_gnf > 0


def test_repayment_is_allocated_oldest_due_date_first(db_session):
    admin, manager, cashier, product, session_ = _setup(db_session)
    customer = customers_service.find_or_create_customer(db_session, "Fatou Camara", "+224600000001")

    sale1 = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.CREDIT, amount_given=1000,
        items=[{"product_id": product.id, "qty": 1}],
        customer_id=customer.id, due_date=date(2026, 9, 15),
    )
    sale2 = sales_service.create_sale(
        db_session, cashier, session_.id, PaymentMode.CREDIT, amount_given=1000,
        items=[{"product_id": product.id, "qty": 1}],
        customer_id=customer.id, due_date=date(2026, 9, 30),
    )

    db_session.refresh(customer)
    # Règle juste assez pour éteindre la première créance (la plus ancienne échéance).
    customers_service.record_repayment(db_session, customer, sale1.remaining_due_gnf, processed_by=manager.id)

    db_session.refresh(sale1)
    db_session.refresh(sale2)
    assert sale1.remaining_due_gnf == 0
    assert sale2.remaining_due_gnf == product.prix_vente - 1000
    assert customers_service.count_active_credits(db_session, customer) == 1


def test_credit_limit_exceeded_logs_a_trace_via_api(db_session, client, auth_headers):
    admin, manager, cashier, product, session_ = _setup(db_session)
    headers = auth_headers("apiadmin", Role.ADMIN)
    customer = customers_service.find_or_create_customer(db_session, "Fatou Camara", "+224600000001")

    for _ in range(2):
        sales_service.create_sale(
            db_session, cashier, session_.id, PaymentMode.CREDIT, amount_given=1000,
            items=[{"product_id": product.id, "qty": 1}],
            customer_id=customer.id,
        )

    res = client.post(
        "/api/sales",
        json={
            "cash_session_id": session_.id,
            "payment_mode": "credit",
            "amount_given": 1000,
            "items": [{"product_id": product.id, "qty": 1}],
            "customer_id": customer.id,
        },
        headers=headers,
    )
    assert res.status_code == 422
    assert "dépassé" in res.json()["detail"]

    from app.models import Log
    log = db_session.query(Log).filter(Log.action == "credit_limit_exceeded").first()
    assert log is not None
