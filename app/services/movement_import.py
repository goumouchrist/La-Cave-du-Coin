import csv
import io
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models import MovementType
from app.services import products as products_service
from app.services import stock as stock_service
from app.services import suppliers as suppliers_service

REQUIRED_COLUMNS = {"barcode", "type", "qty"}
ALLOWED_TYPES = {"entree", "casse", "don", "ajustement"}

CSV_TEMPLATE = (
    "barcode,type,qty,unit,invoice_number,reason,supplier\n"
    "6001234500017,entree,5,carton,F-2026-001,,Brasserie de Guinée\n"
    "6001234500024,casse,2,unite,,Bouteilles cassées à la livraison,\n"
)


@dataclass
class ImportResult:
    created: list[str] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)


def _parse_row(row: dict) -> dict:
    missing = [col for col in REQUIRED_COLUMNS if not (row.get(col) or "").strip()]
    if missing:
        raise ValueError(f"colonnes obligatoires manquantes: {', '.join(missing)}")

    movement_type = row["type"].strip().lower()
    if movement_type not in ALLOWED_TYPES:
        raise ValueError(f"type invalide {movement_type!r} — doit être l'un de : {', '.join(sorted(ALLOWED_TYPES))}")

    try:
        qty = int(row["qty"].strip())
    except ValueError:
        raise ValueError(f"quantité non numérique: {row['qty']!r}")
    if qty <= 0:
        raise ValueError("la quantité doit être supérieure à 0")

    unit = (row.get("unit") or "unite").strip().lower() or "unite"
    if unit not in ("unite", "carton", "pack"):
        raise ValueError(f"unité invalide {unit!r} — doit être unite, carton ou pack")

    return {
        "barcode": row["barcode"].strip(),
        "type": MovementType(movement_type),
        "qty": qty,
        "unit": unit,
        "invoice_number": (row.get("invoice_number") or "").strip() or None,
        "reason": (row.get("reason") or "").strip() or None,
        "supplier_name": (row.get("supplier") or "").strip() or None,
    }


def import_movements_from_csv(db: Session, csv_text: str, created_by: int) -> ImportResult:
    result = ImportResult()
    reader = csv.DictReader(io.StringIO(csv_text))

    for line_number, row in enumerate(reader, start=2):  # ligne 1 = en-tête
        try:
            data = _parse_row(row)
            product = products_service.find_by_barcode(db, data["barcode"])
            if not product:
                raise ValueError(f"produit inconnu pour le code-barres {data['barcode']!r}")

            supplier_id = None
            if data["supplier_name"]:
                supplier_id = suppliers_service.find_or_create_supplier_by_name(db, data["supplier_name"]).id

            stock_service.create_movement(
                db,
                product,
                data["type"],
                data["qty"],
                data["unit"],
                created_by=created_by,
                invoice_number=data["invoice_number"],
                reason=data["reason"],
                supplier_id=supplier_id,
            )
            result.created.append(f"{product.name} ({data['type'].value}, {data['qty']} {data['unit']})")
        except ValueError as exc:
            result.errors.append({"line": line_number, "error": str(exc)})

    return result
