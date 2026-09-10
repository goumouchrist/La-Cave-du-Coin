import csv
import io
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.services import products as products_service
from app.services import suppliers as suppliers_service

REQUIRED_COLUMNS = {"name", "category", "prix_achat", "prix_vente"}
OPTIONAL_DEFAULTS = {
    "barcode": None,
    "unit_carton_qty": 24,
    "unit_pack_qty": 6,
    "stock_min_cartons": 5,
}

CSV_TEMPLATE = (
    "barcode,name,category,unit_carton_qty,unit_pack_qty,prix_achat,prix_vente,stock_min_cartons,supplier\n"
    "6001234500017,Coca-Cola 33cl,Sodas,24,6,3000,5000,5,Brasserie de Guinée\n"
    "6001234500024,Fanta Orange 33cl,Sodas,24,6,3000,5000,5,Brasserie de Guinée\n"
)


@dataclass
class ImportResult:
    created: list[str] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)


def _parse_row(row: dict) -> dict:
    missing = [col for col in REQUIRED_COLUMNS if not (row.get(col) or "").strip()]
    if missing:
        raise ValueError(f"colonnes obligatoires manquantes: {', '.join(missing)}")

    data = dict(OPTIONAL_DEFAULTS)
    data["name"] = row["name"].strip()
    data["category"] = row["category"].strip()
    barcode = (row.get("barcode") or "").strip()
    data["barcode"] = barcode or None

    for int_field in ("unit_carton_qty", "unit_pack_qty", "prix_achat", "prix_vente", "stock_min_cartons"):
        raw = (row.get(int_field) or "").strip()
        if raw:
            try:
                data[int_field] = int(raw)
            except ValueError:
                raise ValueError(f"valeur non numérique pour '{int_field}': {raw!r}")

    return data


def import_products_from_csv(db: Session, csv_text: str) -> ImportResult:
    result = ImportResult()
    reader = csv.DictReader(io.StringIO(csv_text))

    for line_number, row in enumerate(reader, start=2):  # ligne 1 = en-tête
        try:
            data = _parse_row(row)
            supplier_name = (row.get("supplier") or "").strip()
            if supplier_name:
                data["supplier_id"] = suppliers_service.find_or_create_supplier_by_name(db, supplier_name).id
            product = products_service.create_product(db, data)
            result.created.append(product.name)
        except (ValueError, products_service.PriceBelowMinMarginError, products_service.DuplicateBarcodeError) as exc:
            result.errors.append({"line": line_number, "error": str(exc)})

    return result
