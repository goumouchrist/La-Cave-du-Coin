from app.models import MovementStatus, MovementType, Product, Role, StockMovement, Supplier
from app.services.movement_import import import_movements_from_csv
from app.services.products import get_current_stock_units
from app.services.users import create_user


def make_product(db_session, **overrides):
    data = dict(name="Coca-Cola 33cl", category="Sodas", barcode="1111111111111", prix_achat=3000, prix_vente=5000)
    data.update(overrides)
    product = Product(**data)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def test_import_creates_pending_entree_movement(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    product = make_product(db_session)

    csv_text = "barcode,type,qty,unit,invoice_number,reason,supplier\n1111111111111,entree,5,carton,F-001,,\n"
    result = import_movements_from_csv(db_session, csv_text, created_by=admin.id)

    assert len(result.created) == 1
    assert result.errors == []

    movement = db_session.query(StockMovement).first()
    assert movement.type == MovementType.ENTREE
    assert movement.qty_units == 120
    assert movement.status == MovementStatus.PENDING
    assert movement.invoice_number == "F-001"
    assert get_current_stock_units(db_session, product.id) == 0, "pas encore validé"


def test_import_links_supplier_by_name_and_creates_it(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    make_product(db_session)

    csv_text = "barcode,type,qty,unit,invoice_number,reason,supplier\n1111111111111,entree,5,carton,,,Brasserie de Guinée\n"
    import_movements_from_csv(db_session, csv_text, created_by=admin.id)

    movement = db_session.query(StockMovement).first()
    supplier = db_session.query(Supplier).first()
    assert supplier.name == "Brasserie de Guinée"
    assert movement.supplier_id == supplier.id


def test_import_reports_unknown_barcode(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)

    csv_text = "barcode,type,qty\n9999999999999,entree,5\n"
    result = import_movements_from_csv(db_session, csv_text, created_by=admin.id)

    assert result.created == []
    assert "inconnu" in result.errors[0]["error"]


def test_import_reports_invalid_type(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    make_product(db_session)

    csv_text = "barcode,type,qty\n1111111111111,sortie_vente,5\n"
    result = import_movements_from_csv(db_session, csv_text, created_by=admin.id)

    assert result.created == []
    assert "invalide" in result.errors[0]["error"]


def test_import_reports_zero_or_negative_quantity(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    make_product(db_session)

    csv_text = "barcode,type,qty\n1111111111111,entree,0\n"
    result = import_movements_from_csv(db_session, csv_text, created_by=admin.id)

    assert result.created == []
    assert "supérieure à 0" in result.errors[0]["error"]


def test_import_parses_expiry_date(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    make_product(db_session)

    csv_text = "barcode,type,qty,unit,invoice_number,expiry_date,reason,supplier\n1111111111111,entree,5,carton,,2026-12-31,,\n"
    result = import_movements_from_csv(db_session, csv_text, created_by=admin.id)

    assert result.errors == []
    movement = db_session.query(StockMovement).first()
    assert str(movement.expiry_date) == "2026-12-31"


def test_import_reports_invalid_expiry_date_format(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    make_product(db_session)

    csv_text = "barcode,type,qty,expiry_date\n1111111111111,entree,5,31/12/2026\n"
    result = import_movements_from_csv(db_session, csv_text, created_by=admin.id)

    assert result.created == []
    assert "péremption" in result.errors[0]["error"]


def test_import_defaults_unit_to_unite(db_session):
    admin = create_user(db_session, "admin", "pw", Role.ADMIN)
    make_product(db_session)

    csv_text = "barcode,type,qty\n1111111111111,entree,5\n"
    import_movements_from_csv(db_session, csv_text, created_by=admin.id)

    movement = db_session.query(StockMovement).first()
    assert movement.qty_units == 5
