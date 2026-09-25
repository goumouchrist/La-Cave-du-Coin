from datetime import date, timedelta

import pytest

from app.models import PaymentMode, Product, QuoteStatus, Role
from app.services import cash as cash_service
from app.services import customers as customers_service
from app.services import products as products_service
from app.services import quotes as quotes_service
from app.services import sales as sales_service
from app.services.users import create_user

CUSTOMER_NAME = "Client Test"
CUSTOMER_PHONE = "600000000"


def setup_product_with_stock(db_session, admin, manager, qty_units=100, prix_vente=5000, prix_achat=3000):
    from app.models import MovementType
    from app.services import stock as stock_service

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


def test_create_quote_without_cash_session_succeeds(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)

    quote = quotes_service.create_quote(
        db_session, cashier, items=[{"product_id": product.id, "qty": 3}],
        customer_name=CUSTOMER_NAME, customer_phone=CUSTOMER_PHONE,
    )

    assert quote.status == QuoteStatus.EN_COURS
    assert quote.total_amount == 3 * product.prix_vente
    assert quote.expires_at == date.today() + timedelta(days=15)


def test_create_quote_requires_customer_name_and_phone(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)

    with pytest.raises(quotes_service.CustomerInfoRequiredError):
        quotes_service.create_quote(db_session, cashier, items=[{"product_id": product.id, "qty": 1}])

    with pytest.raises(quotes_service.CustomerInfoRequiredError):
        quotes_service.create_quote(
            db_session, cashier, items=[{"product_id": product.id, "qty": 1}], customer_name="   ", customer_phone=CUSTOMER_PHONE,
        )

    with pytest.raises(quotes_service.CustomerInfoRequiredError):
        quotes_service.create_quote(
            db_session, cashier, items=[{"product_id": product.id, "qty": 1}], customer_name=CUSTOMER_NAME, customer_phone="",
        )


def test_create_quote_with_existing_customer_id_bypasses_name_phone(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    customer = customers_service.find_or_create_customer(db_session, "Client Existant", "611111111")

    quote = quotes_service.create_quote(db_session, cashier, items=[{"product_id": product.id, "qty": 1}], customer_id=customer.id)
    assert quote.customer_id == customer.id


def test_create_quote_more_than_five_identical_items_requires_confirmation(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)

    with pytest.raises(quotes_service.QuantityConfirmationRequiredError):
        quotes_service.create_quote(
            db_session, cashier, items=[{"product_id": product.id, "qty": 6}],
            customer_name=CUSTOMER_NAME, customer_phone=CUSTOMER_PHONE,
        )

    quote = quotes_service.create_quote(
        db_session, cashier, items=[{"product_id": product.id, "qty": 6, "quantity_confirmed": True}],
        customer_name=CUSTOMER_NAME, customer_phone=CUSTOMER_PHONE,
    )
    assert quote.total_amount == 6 * product.prix_vente

    # La confirmation faite à la création du devis suffit : la conversion ne
    # doit pas re-bloquer sur le même seuil anti-fraude.
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    sale = quotes_service.convert_to_sale(db_session, quote, cashier, session_.id, PaymentMode.ESPECES, amount_given=100000)
    assert sale.total_amount == 6 * product.prix_vente


def test_quote_number_is_short_and_unique(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)

    numbers = set()
    for _ in range(20):
        quote = quotes_service.create_quote(
            db_session, cashier, items=[{"product_id": product.id, "qty": 1}],
            customer_name=CUSTOMER_NAME, customer_phone=CUSTOMER_PHONE,
        )
        assert quote.quote_number.startswith("DEV-")
        assert len(quote.quote_number) == len("DEV-") + 5
        numbers.add(quote.quote_number)
    assert len(numbers) == 20  # jamais de collision sur 20 générations


def test_create_quote_unknown_product_raises(db_session):
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)

    with pytest.raises(quotes_service.ProductNotFoundError):
        quotes_service.create_quote(
            db_session, cashier, items=[{"product_id": 999, "qty": 1}],
            customer_name=CUSTOMER_NAME, customer_phone=CUSTOMER_PHONE,
        )


def test_convert_quote_requires_open_cash_session(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    quote = quotes_service.create_quote(
        db_session, cashier, items=[{"product_id": product.id, "qty": 1}],
        customer_name=CUSTOMER_NAME, customer_phone=CUSTOMER_PHONE,
    )

    with pytest.raises(sales_service.CashSessionClosedError):
        quotes_service.convert_to_sale(db_session, quote, cashier, 999, PaymentMode.ESPECES, amount_given=5000)


def test_convert_quote_uses_snapshotted_price(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager, prix_vente=5000)
    quote = quotes_service.create_quote(
        db_session, cashier, items=[{"product_id": product.id, "qty": 2}],
        customer_name=CUSTOMER_NAME, customer_phone=CUSTOMER_PHONE,
    )
    assert quote.total_amount == 10000

    product.prix_vente = 6000
    db_session.commit()

    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    sale = quotes_service.convert_to_sale(db_session, quote, cashier, session_.id, PaymentMode.ESPECES, amount_given=10000)

    assert sale.total_amount == 10000
    assert sale.items[0].unit_price == 5000
    db_session.refresh(quote)
    assert quote.status == QuoteStatus.CONVERTI
    assert quote.converted_sale_id == sale.id


def test_convert_quote_decrements_stock(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager, qty_units=100)
    quote = quotes_service.create_quote(
        db_session, cashier, items=[{"product_id": product.id, "qty": 4}],
        customer_name=CUSTOMER_NAME, customer_phone=CUSTOMER_PHONE,
    )
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)

    quotes_service.convert_to_sale(db_session, quote, cashier, session_.id, PaymentMode.ESPECES, amount_given=20000)

    assert products_service.get_current_stock_units(db_session, product.id) == 96


def test_convert_already_converted_quote_raises(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    quote = quotes_service.create_quote(
        db_session, cashier, items=[{"product_id": product.id, "qty": 1}],
        customer_name=CUSTOMER_NAME, customer_phone=CUSTOMER_PHONE,
    )
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)
    quotes_service.convert_to_sale(db_session, quote, cashier, session_.id, PaymentMode.ESPECES, amount_given=5000)

    with pytest.raises(quotes_service.QuoteNotConvertibleError):
        quotes_service.convert_to_sale(db_session, quote, cashier, session_.id, PaymentMode.ESPECES, amount_given=5000)


def test_convert_expired_quote_raises_and_marks_expired(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    quote = quotes_service.create_quote(
        db_session, cashier, items=[{"product_id": product.id, "qty": 1}], validity_days=-1,
        customer_name=CUSTOMER_NAME, customer_phone=CUSTOMER_PHONE,
    )
    session_ = cash_service.open_session(db_session, cashier.id, opening_amount=0)

    with pytest.raises(quotes_service.QuoteNotConvertibleError):
        quotes_service.convert_to_sale(db_session, quote, cashier, session_.id, PaymentMode.ESPECES, amount_given=5000)

    db_session.refresh(quote)
    assert quote.status == QuoteStatus.EXPIRE


def test_cancel_quote_then_recancel_raises(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)
    product = setup_product_with_stock(db_session, admin, manager)
    quote = quotes_service.create_quote(
        db_session, cashier, items=[{"product_id": product.id, "qty": 1}],
        customer_name=CUSTOMER_NAME, customer_phone=CUSTOMER_PHONE,
    )

    cancelled = quotes_service.cancel_quote(db_session, quote)
    assert cancelled.status == QuoteStatus.ANNULE

    with pytest.raises(quotes_service.QuoteNotConvertibleError):
        quotes_service.cancel_quote(db_session, quote)


def test_http_create_then_convert_quote(client, auth_headers, db_session):
    headers = auth_headers("cashier", Role.CAISSIER)
    admin = create_user(db_session, "admin", "pw2", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw2", Role.MANAGER)
    product = setup_product_with_stock(db_session, admin, manager)

    res = client.post(
        "/api/quotes",
        json={"items": [{"product_id": product.id, "qty": 2}], "customer_name": CUSTOMER_NAME, "customer_phone": CUSTOMER_PHONE},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    quote = res.json()

    res = client.post(
        f"/api/quotes/{quote['id']}/convert",
        json={"cash_session_id": 999, "payment_mode": "especes", "amount_given": 10000},
        headers=headers,
    )
    assert res.status_code == 422

    open_res = client.post("/api/cash-sessions/open", json={"opening_amount": 0}, headers=headers)
    assert open_res.status_code == 201, open_res.text
    session_id = open_res.json()["id"]

    res = client.post(
        f"/api/quotes/{quote['id']}/convert",
        json={"cash_session_id": session_id, "payment_mode": "especes", "amount_given": 10000},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    sale = res.json()
    assert sale["total_amount"] == 2 * product.prix_vente


def test_http_create_quote_without_customer_info_is_rejected(client, auth_headers, db_session):
    headers = auth_headers("cashier", Role.CAISSIER)
    admin = create_user(db_session, "admin", "pw2", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw2", Role.MANAGER)
    product = setup_product_with_stock(db_session, admin, manager)

    res = client.post("/api/quotes", json={"items": [{"product_id": product.id, "qty": 1}]}, headers=headers)
    assert res.status_code == 422, res.text


def test_get_quote_by_number(client, auth_headers, db_session):
    headers = auth_headers("cashier", Role.CAISSIER)
    admin = create_user(db_session, "admin", "pw2", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw2", Role.MANAGER)
    product = setup_product_with_stock(db_session, admin, manager)

    created = client.post(
        "/api/quotes",
        json={"items": [{"product_id": product.id, "qty": 1}], "customer_name": CUSTOMER_NAME, "customer_phone": CUSTOMER_PHONE},
        headers=headers,
    ).json()

    res = client.get(f"/api/quotes/by-number/{created['quote_number']}", headers=headers)
    assert res.status_code == 200, res.text
    assert res.json()["id"] == created["id"]

    res = client.get("/api/quotes/by-number/DEV-UNKNOWN", headers=headers)
    assert res.status_code == 404


def test_quote_pdf_endpoint_returns_pdf(client, auth_headers, db_session):
    headers = auth_headers("cashier", Role.CAISSIER)
    admin = create_user(db_session, "admin", "pw2", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw2", Role.MANAGER)
    product = setup_product_with_stock(db_session, admin, manager)

    res = client.post(
        "/api/quotes",
        json={"items": [{"product_id": product.id, "qty": 1}], "customer_name": CUSTOMER_NAME, "customer_phone": CUSTOMER_PHONE},
        headers=headers,
    )
    quote_id = res.json()["id"]

    pdf_res = client.get(f"/api/quotes/{quote_id}/pdf", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content[:4] == b"%PDF"
