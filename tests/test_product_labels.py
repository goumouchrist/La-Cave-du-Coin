import pytest

from app.models import Product
from app.services import labels as labels_service
from app.services import products as products_service


def make_product(db_session, **overrides):
    data = dict(name="Jus local 1L", category="Jus", prix_achat=3000, prix_vente=5000, barcode=None)
    data.update(overrides)
    product = Product(**data)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def test_generate_internal_barcode_for_product_without_one(db_session):
    product = make_product(db_session)

    products_service.generate_internal_barcode(db_session, product)

    assert product.barcode == f"INT{product.id:08d}"


def test_generate_internal_barcode_is_unique_per_product(db_session):
    p1 = make_product(db_session, name="Produit A")
    p2 = make_product(db_session, name="Produit B")

    products_service.generate_internal_barcode(db_session, p1)
    products_service.generate_internal_barcode(db_session, p2)

    assert p1.barcode != p2.barcode


def test_cannot_overwrite_existing_barcode_without_force(db_session):
    product = make_product(db_session, barcode="6001234500017")

    with pytest.raises(products_service.BarcodeAlreadySetError):
        products_service.generate_internal_barcode(db_session, product)

    assert product.barcode == "6001234500017"


def test_can_overwrite_existing_barcode_with_force(db_session):
    product = make_product(db_session, barcode="6001234500017")

    products_service.generate_internal_barcode(db_session, product, force=True)

    assert product.barcode == f"INT{product.id:08d}"


def test_build_product_label_pdf(db_session):
    product = make_product(db_session)
    products_service.generate_internal_barcode(db_session, product)

    pdf_bytes = labels_service.build_product_label_pdf(product)

    assert pdf_bytes[:4] == b"%PDF"
