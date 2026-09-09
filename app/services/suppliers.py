from sqlalchemy.orm import Session

from app.models import MovementStatus, MovementType, StockMovement, Supplier


def create_supplier(db: Session, name: str, phone: str | None, address: str | None) -> Supplier:
    supplier = Supplier(name=name, phone=phone, address=address)
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def list_suppliers(db: Session) -> list[Supplier]:
    return db.query(Supplier).filter(Supplier.is_active.is_(True)).all()


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
