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
