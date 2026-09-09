from app.models import Product
from app.services.product_import import import_products_from_csv


def test_import_creates_products_from_valid_rows(db_session):
    csv_text = (
        "barcode,name,category,unit_carton_qty,unit_pack_qty,prix_achat,prix_vente,stock_min_cartons\n"
        "1111111111111,Coca-Cola 33cl,Sodas,24,6,3000,5000,5\n"
        "2222222222222,Fanta Orange 33cl,Sodas,24,6,3000,5000,5\n"
    )

    result = import_products_from_csv(db_session, csv_text)

    assert result.created == ["Coca-Cola 33cl", "Fanta Orange 33cl"]
    assert result.errors == []
    assert db_session.query(Product).count() == 2


def test_import_uses_defaults_for_optional_columns(db_session):
    csv_text = "name,category,prix_achat,prix_vente\nEau minérale 1.5L,Eaux,2000,3500\n"

    result = import_products_from_csv(db_session, csv_text)

    assert result.created == ["Eau minérale 1.5L"]
    product = db_session.query(Product).first()
    assert product.unit_carton_qty == 24
    assert product.unit_pack_qty == 6
    assert product.stock_min_cartons == 5
    assert product.barcode is None


def test_import_reports_missing_required_columns(db_session):
    csv_text = "name,category,prix_achat,prix_vente\n,Sodas,3000,5000\n"

    result = import_products_from_csv(db_session, csv_text)

    assert result.created == []
    assert len(result.errors) == 1
    assert result.errors[0]["line"] == 2
    assert "manquantes" in result.errors[0]["error"]


def test_import_reports_price_below_margin_but_continues_other_rows(db_session):
    csv_text = (
        "name,category,prix_achat,prix_vente\n"
        "Produit sous-facturé,Sodas,3000,1000\n"
        "Produit correct,Sodas,3000,5000\n"
    )

    result = import_products_from_csv(db_session, csv_text)

    assert result.created == ["Produit correct"]
    assert len(result.errors) == 1
    assert result.errors[0]["line"] == 2


def test_import_reports_duplicate_barcode(db_session):
    db_session.add(Product(name="Existant", category="Sodas", barcode="1111111111111", prix_achat=3000, prix_vente=5000))
    db_session.commit()

    csv_text = "barcode,name,category,prix_achat,prix_vente\n1111111111111,Doublon,Sodas,3000,5000\n"
    result = import_products_from_csv(db_session, csv_text)

    assert result.created == []
    assert "déjà utilisé" in result.errors[0]["error"]


def test_import_reports_non_numeric_price(db_session):
    csv_text = "name,category,prix_achat,prix_vente\nProduit invalide,Sodas,abc,5000\n"
    result = import_products_from_csv(db_session, csv_text)

    assert result.created == []
    assert "non numérique" in result.errors[0]["error"]
