import pytest

from app.models import MovementType, Product, Role
from app.services import products as products_service
from app.services import stock as stock_service
from app.services.users import create_user


def make_product(db_session, **overrides):
    data = dict(
        name="Coca-Cola 33cl",
        category="Sodas",
        barcode="1234567890123",
        unit_carton_qty=24,
        unit_pack_qty=6,
        prix_achat=3000,
        prix_vente=5000,
        stock_min_cartons=5,
    )
    data.update(overrides)
    product = Product(**data)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def test_deactivate_product_hides_it_and_frees_barcode(db_session):
    product = make_product(db_session, barcode="6001234500017")

    products_service.deactivate_product(db_session, product)

    assert product.is_active is False
    assert product.barcode is None

    # Le code-barres libéré peut être réutilisé par un nouveau produit actif
    new_product = products_service.create_product(
        db_session,
        dict(
            name="Nouveau produit", category="Sodas", barcode="6001234500017",
            unit_carton_qty=24, unit_pack_qty=6, prix_achat=3000, prix_vente=5000, stock_min_cartons=5,
        ),
    )
    assert new_product.barcode == "6001234500017"


def test_unit_conversion_carton_and_pack(db_session):
    product = make_product(db_session)
    assert products_service.convert_to_units(product, 2, "carton") == 48
    assert products_service.convert_to_units(product, 3, "pack") == 18
    assert products_service.convert_to_units(product, 10, "unite") == 10


def test_price_below_minimum_margin_is_blocked():
    with pytest.raises(products_service.PriceBelowMinMarginError):
        products_service.validate_price(prix_achat=1000, prix_vente=900)


def test_price_below_minimum_margin_allowed_with_promo_flag():
    products_service.validate_price(prix_achat=1000, prix_vente=900, is_promo=True)


def test_duplicate_active_barcode_is_rejected(db_session):
    make_product(db_session, barcode="9999999999999")
    with pytest.raises(products_service.DuplicateBarcodeError):
        products_service.create_product(
            db_session,
            dict(
                name="Autre produit",
                category="Sodas",
                barcode="9999999999999",
                unit_carton_qty=24,
                unit_pack_qty=6,
                prix_achat=1000,
                prix_vente=1500,
                stock_min_cartons=5,
            ),
        )


def test_entree_movement_increases_stock_only_after_validation(db_session):
    product = make_product(db_session)
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)

    movement = stock_service.create_movement(
        db_session, product, MovementType.ENTREE, qty=2, unit="carton", created_by=admin.id, invoice_number="F-001"
    )
    assert movement.qty_units == 48
    assert products_service.get_current_stock_units(db_session, product.id) == 0, "pas encore validé"

    stock_service.validate_movement(db_session, movement, manager, approve=True)
    assert products_service.get_current_stock_units(db_session, product.id) == 48


def test_movement_cannot_be_self_validated(db_session):
    product = make_product(db_session)
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)

    movement = stock_service.create_movement(db_session, product, MovementType.ENTREE, qty=1, unit="carton", created_by=admin.id)
    with pytest.raises(stock_service.SelfValidationError):
        stock_service.validate_movement(db_session, movement, admin, approve=True)


def test_ajustement_requires_admin_validator(db_session):
    product = make_product(db_session)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    other_manager = create_user(db_session, "manager2", "pw", Role.MANAGER)

    movement = stock_service.create_movement(
        db_session, product, MovementType.AJUSTEMENT, qty=5, unit="unite", created_by=manager.id, reason="Double comptage"
    )
    with pytest.raises(stock_service.ValidatorRoleError):
        stock_service.validate_movement(db_session, movement, other_manager, approve=True)


def test_negative_ajustement_decreases_stock_after_validation(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    product = make_product(db_session)

    entry = stock_service.create_movement(db_session, product, MovementType.ENTREE, qty=100, unit="unite", created_by=admin.id)
    stock_service.validate_movement(db_session, entry, manager, approve=True)
    assert products_service.get_current_stock_units(db_session, product.id) == 100

    shortage = stock_service.create_movement(
        db_session, product, MovementType.AJUSTEMENT, qty=-12, unit="unite", created_by=manager.id,
        reason="Comptage physique du 2026-09-25 : -12 unités constatées vs stock système",
    )
    stock_service.validate_movement(db_session, shortage, admin, approve=True)
    assert products_service.get_current_stock_units(db_session, product.id) == 88


def test_only_ajustement_can_be_negative(db_session):
    product = make_product(db_session)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)

    with pytest.raises(stock_service.InvalidQuantityError):
        stock_service.create_movement(db_session, product, MovementType.CASSE, qty=-3, unit="unite", created_by=manager.id)

    with pytest.raises(stock_service.InvalidQuantityError):
        stock_service.create_movement(db_session, product, MovementType.AJUSTEMENT, qty=0, unit="unite", created_by=manager.id)


def test_caissier_cannot_validate_movement(db_session):
    product = make_product(db_session)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    cashier = create_user(db_session, "cashier", "pw", Role.CAISSIER)

    movement = stock_service.create_movement(db_session, product, MovementType.CASSE, qty=1, unit="unite", created_by=manager.id, reason="Bouteille cassée")
    with pytest.raises(stock_service.ValidatorRoleError):
        stock_service.validate_movement(db_session, movement, cashier, approve=True)
