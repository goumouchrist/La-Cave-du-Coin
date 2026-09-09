from app.models import MovementType, Product, Role
from app.services import stock as stock_service
from app.services import suppliers as suppliers_service
from app.services.users import create_user


def test_create_supplier(db_session):
    supplier = suppliers_service.create_supplier(db_session, "Brasserie de Guinée", "+224600000010", "Conakry, Zone industrielle")
    assert supplier.id is not None
    assert supplier.name == "Brasserie de Guinée"
    assert supplier.is_active is True


def test_list_suppliers_excludes_inactive(db_session):
    active = suppliers_service.create_supplier(db_session, "Fournisseur A", None, None)
    inactive = suppliers_service.create_supplier(db_session, "Fournisseur B", None, None)
    inactive.is_active = False
    db_session.commit()

    suppliers = suppliers_service.list_suppliers(db_session)
    names = [s.name for s in suppliers]
    assert "Fournisseur A" in names
    assert "Fournisseur B" not in names


def test_product_can_be_linked_to_a_supplier(db_session):
    supplier = suppliers_service.create_supplier(db_session, "Brasserie de Guinée", None, None)
    product = Product(
        name="Guinness 33cl", category="Bières", prix_achat=4500, prix_vente=7000,
        supplier_id=supplier.id,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    assert product.supplier_id == supplier.id
    assert product.supplier.name == "Brasserie de Guinée"


def test_delivery_history_tracks_validated_entries_for_a_supplier(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    supplier = suppliers_service.create_supplier(db_session, "Brasserie de Guinée", "+224600000010", None)
    product = Product(name="Guinness 33cl", category="Bières", prix_achat=4500, prix_vente=7000)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    movement = stock_service.create_movement(
        db_session, product, MovementType.ENTREE, qty=5, unit="carton",
        created_by=admin.id, invoice_number="F-2026-042", supplier_id=supplier.id,
    )

    history_before_validation = suppliers_service.delivery_history(db_session, supplier.id)
    assert history_before_validation == [], "un mouvement en attente ne doit pas apparaître dans l'historique"

    stock_service.validate_movement(db_session, movement, manager, approve=True)

    history = suppliers_service.delivery_history(db_session, supplier.id)
    assert len(history) == 1
    assert history[0].invoice_number == "F-2026-042"
    assert history[0].qty_units == 120


def test_delivery_history_is_scoped_to_the_right_supplier(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    manager = create_user(db_session, "manager", "pw", Role.MANAGER)
    supplier_a = suppliers_service.create_supplier(db_session, "Fournisseur A", None, None)
    supplier_b = suppliers_service.create_supplier(db_session, "Fournisseur B", None, None)
    product = Product(name="Coca-Cola 33cl", category="Sodas", prix_achat=3000, prix_vente=5000)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    movement = stock_service.create_movement(
        db_session, product, MovementType.ENTREE, qty=2, unit="carton",
        created_by=admin.id, supplier_id=supplier_a.id,
    )
    stock_service.validate_movement(db_session, movement, manager, approve=True)

    assert len(suppliers_service.delivery_history(db_session, supplier_a.id)) == 1
    assert len(suppliers_service.delivery_history(db_session, supplier_b.id)) == 0
