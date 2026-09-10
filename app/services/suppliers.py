from sqlalchemy.orm import Session

from app.models import MovementStatus, MovementType, StockMovement, Supplier


def create_supplier(db: Session, name: str, phone: str | None, address: str | None) -> Supplier:
    supplier = Supplier(name=name, phone=phone, address=address)
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def find_or_create_supplier_by_name(db: Session, name: str) -> Supplier:
    """Recherche insensible à la casse ; crée le fournisseur s'il n'existe pas
    encore (utilisé par les imports CSV, où on ne connaît que le nom)."""
    existing = db.query(Supplier).filter(Supplier.name.ilike(name.strip())).first()
    if existing:
        return existing
    return create_supplier(db, name.strip(), None, None)


def list_suppliers(db: Session) -> list[Supplier]:
    return db.query(Supplier).filter(Supplier.is_active.is_(True)).all()


def deactivate_supplier(db: Session, supplier: Supplier) -> Supplier:
    """Désactive le fournisseur (suppression logique) plutôt qu'une suppression
    physique, pour ne jamais casser l'historique des livraisons déjà enregistrées."""
    supplier.is_active = False
    db.commit()
    db.refresh(supplier)
    return supplier


def delivery_history(db: Session, supplier_id: int) -> list[StockMovement]:
    """Historique des réceptions (entrées) validées pour ce fournisseur, plus récentes en premier."""
    return (
        db.query(StockMovement)
        .filter(
            StockMovement.supplier_id == supplier_id,
            StockMovement.type == MovementType.ENTREE,
            StockMovement.status == MovementStatus.VALIDATED,
        )
        .order_by(StockMovement.created_at.desc())
        .all()
    )
