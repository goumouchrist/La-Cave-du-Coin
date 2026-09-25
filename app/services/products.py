from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import MovementStatus, MovementType, Product, StockMovement

UNIT_UNITE = "unite"
UNIT_CARTON = "carton"
UNIT_PACK = "pack"


class PriceBelowMinMarginError(Exception):
    pass


class DuplicateBarcodeError(Exception):
    pass


class BarcodeAlreadySetError(Exception):
    pass


def convert_to_units(product: Product, qty: int, unit: str) -> int:
    """Convertit une quantité exprimée en carton/pack/unité vers l'unité de base."""
    if unit == UNIT_CARTON:
        return qty * product.unit_carton_qty
    if unit == UNIT_PACK:
        return qty * product.unit_pack_qty
    return qty


def validate_price(prix_achat: int, prix_vente: int, is_promo: bool = False) -> None:
    min_price = prix_achat * settings.MIN_MARGIN_RATIO
    if prix_vente < min_price and not is_promo:
        raise PriceBelowMinMarginError(
            f"Prix de vente ({prix_vente}) inférieur au minimum autorisé "
            f"({min_price:.0f} = prix d'achat - {int((1 - settings.MIN_MARGIN_RATIO) * 100)}%)"
        )


def get_current_stock_units(db: Session, product_id: int) -> int:
    entree_types = (MovementType.ENTREE, MovementType.RETOUR)
    sortie_types = (MovementType.SORTIE_VENTE, MovementType.CASSE, MovementType.DON)

    in_qty = db.query(func.coalesce(func.sum(StockMovement.qty_units), 0)).filter(
        StockMovement.product_id == product_id,
        StockMovement.type.in_(entree_types),
        StockMovement.status == MovementStatus.VALIDATED,
    ).scalar()

    out_qty = db.query(func.coalesce(func.sum(StockMovement.qty_units), 0)).filter(
        StockMovement.product_id == product_id,
        StockMovement.type.in_(sortie_types),
        StockMovement.status == MovementStatus.VALIDATED,
    ).scalar()

    adjustments = db.query(func.coalesce(func.sum(StockMovement.qty_units), 0)).filter(
        StockMovement.product_id == product_id,
        StockMovement.type == MovementType.AJUSTEMENT,
        StockMovement.status == MovementStatus.VALIDATED,
    ).scalar()

    return int(in_qty) - int(out_qty) + int(adjustments)


def _get_consumed_units(db: Session, product_id: int) -> int:
    """Unités sorties du stock (ventes + casse + don, plus les ajustements
    négatifs en valeur absolue), validées — utilisé pour répartir la
    consommation sur les lots d'entrée (FEFO, voir get_batches_remaining)."""
    sortie_types = (MovementType.SORTIE_VENTE, MovementType.CASSE, MovementType.DON)
    out_qty = db.query(func.coalesce(func.sum(StockMovement.qty_units), 0)).filter(
        StockMovement.product_id == product_id,
        StockMovement.type.in_(sortie_types),
        StockMovement.status == MovementStatus.VALIDATED,
    ).scalar()

    negative_adjustments = db.query(func.coalesce(func.sum(StockMovement.qty_units), 0)).filter(
        StockMovement.product_id == product_id,
        StockMovement.type == MovementType.AJUSTEMENT,
        StockMovement.status == MovementStatus.VALIDATED,
        StockMovement.qty_units < 0,
    ).scalar()

    return int(out_qty) - int(negative_adjustments)


def get_batches_remaining(db: Session, product_id: int) -> list[dict]:
    """Répartit la consommation totale sur les lots d'entrée validés, du plus
    proche de la péremption au plus lointain (lots sans date en dernier) —
    méthode FEFO (First Expired, First Out). Les retours clients et les
    ajustements positifs (surplus) réintègrent du stock sans date de
    péremption connue et ne sont donc pas rattachés à un lot : si la
    consommation dépasse le total des lots datés, le surplus est simplement
    absorbé (lots à 0, jamais négatifs)."""
    batches = (
        db.query(StockMovement)
        .filter(
            StockMovement.product_id == product_id,
            StockMovement.type == MovementType.ENTREE,
            StockMovement.status == MovementStatus.VALIDATED,
        )
        .order_by(StockMovement.expiry_date.is_(None), StockMovement.expiry_date.asc(), StockMovement.created_at.asc())
        .all()
    )

    remaining_to_deplete = _get_consumed_units(db, product_id)
    result = []
    for batch in batches:
        consumed_here = min(batch.qty_units, remaining_to_deplete)
        remaining_to_deplete -= consumed_here
        result.append({
            "movement_id": batch.id,
            "expiry_date": batch.expiry_date,
            "qty_units": batch.qty_units,
            "remaining_units": batch.qty_units - consumed_here,
        })
    return result


def create_product(db: Session, data: dict, is_promo: bool = False) -> Product:
    validate_price(data["prix_achat"], data["prix_vente"], is_promo)
    if data.get("barcode"):
        existing = db.query(Product).filter(
            Product.barcode == data["barcode"], Product.is_active.is_(True)
        ).first()
        if existing:
            raise DuplicateBarcodeError(f"Le code-barres {data['barcode']} est déjà utilisé par un produit actif")
    product = Product(**data)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def deactivate_product(db: Session, product: Product) -> Product:
    """Désactive le produit (suppression logique) : il n'apparaît plus dans le
    catalogue/la caisse, mais son historique de ventes et de mouvements reste
    intact pour la traçabilité. Le code-barres est libéré (mis à None) pour
    pouvoir être réutilisé par un nouveau produit sans violer la contrainte
    d'unicité en base."""
    product.is_active = False
    product.barcode = None
    db.commit()
    db.refresh(product)
    return product


def generate_internal_barcode(db: Session, product: Product, force: bool = False) -> Product:
    """Attribue un code interne unique (QR code) à un produit qui n'a pas de
    code-barres fournisseur — basé sur l'id du produit, donc toujours unique
    sans avoir besoin de vérifier les doublons."""
    if product.barcode and not force:
        raise BarcodeAlreadySetError(
            f"Le produit '{product.name}' a déjà un code-barres ({product.barcode}) — "
            "utilisez force=true pour le remplacer."
        )
    product.barcode = f"INT{product.id:08d}"
    db.commit()
    db.refresh(product)
    return product


def find_by_barcode(db: Session, barcode: str) -> Product | None:
    return db.query(Product).filter(Product.barcode == barcode, Product.is_active.is_(True)).first()


def is_below_alert_threshold(db: Session, product: Product) -> bool:
    stock_units = get_current_stock_units(db, product.id)
    min_units = product.stock_min_cartons * product.unit_carton_qty
    return stock_units < min_units
