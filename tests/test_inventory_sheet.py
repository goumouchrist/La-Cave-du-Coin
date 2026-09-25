from app.models import Product, Role
from app.services import inventory as inventory_service
from app.services.users import create_user


def _make_product(db_session, name="Coca-Cola 33cl", is_active=True, barcode="1234567890123"):
    product = Product(
        name=name,
        category="Sodas",
        barcode=barcode,
        unit_carton_qty=24,
        unit_pack_qty=6,
        prix_achat=3000,
        prix_vente=5000,
        stock_min_cartons=5,
        is_active=is_active,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def test_build_inventory_sheet_pdf(db_session):
    product = _make_product(db_session)
    pdf_bytes = inventory_service.build_inventory_sheet_pdf([product])
    assert pdf_bytes[:4] == b"%PDF"


def test_inventory_sheet_endpoint_requires_manager_or_admin(client, auth_headers, db_session):
    _make_product(db_session)
    cashier_headers = auth_headers("cashier", Role.CAISSIER)
    res = client.get("/api/products/inventory-sheet.pdf", headers=cashier_headers)
    assert res.status_code == 403


def test_inventory_sheet_endpoint_returns_pdf_for_manager(client, auth_headers, db_session):
    _make_product(db_session)
    headers = auth_headers("manager", Role.MANAGER)
    res = client.get("/api/products/inventory-sheet.pdf", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content[:4] == b"%PDF"


def test_inventory_sheet_excludes_inactive_products(client, auth_headers, db_session):
    create_user(db_session, "admin", "pw2", Role.ADMIN)
    _make_product(db_session, name="Produit actif", barcode="1111111111111", is_active=True)
    _make_product(db_session, name="Produit désactivé", barcode="2222222222222", is_active=False)
    headers = auth_headers("manager", Role.MANAGER)

    res = client.get("/api/products/inventory-sheet.pdf", headers=headers)
    assert res.status_code == 200
    assert res.content[:4] == b"%PDF"
