from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import Role, Supplier, User
from app.schemas import StockMovementOut, SupplierCreate, SupplierOut
from app.services import suppliers as suppliers_service

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.post("", response_model=SupplierOut, status_code=status.HTTP_201_CREATED)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN, Role.MANAGER))):
    supplier = suppliers_service.create_supplier(db, payload.name, payload.phone, payload.address)
    return supplier


@router.get("", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN, Role.MANAGER, Role.CAISSIER))):
    return suppliers_service.list_suppliers(db)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(supplier_id: int, db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN, Role.MANAGER))):
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fournisseur introuvable")
    suppliers_service.deactivate_supplier(db, supplier)


@router.get("/{supplier_id}/movements", response_model=list[StockMovementOut])
def supplier_delivery_history(supplier_id: int, db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN, Role.MANAGER))):
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fournisseur introuvable")
    return suppliers_service.delivery_history(db, supplier_id)
