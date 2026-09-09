from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import client_ip, get_current_user, require_role
from app.models import Product, Role, StockMovement, User
from app.schemas import ProductOut, StockMovementCreate, StockMovementOut, StockMovementValidate
from app.services import logs as logs_service
from app.services import products as products_service
from app.services import stock as stock_service

router = APIRouter(prefix="/api/stock", tags=["stock"])


@router.post("/movements", response_model=StockMovementOut, status_code=status.HTTP_201_CREATED)
def create_movement(
    payload: StockMovementCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.MANAGER)),
):
    product = db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produit introuvable")

    movement = stock_service.create_movement(
        db,
        product,
        payload.type,
        payload.qty,
        payload.unit,
        created_by=current_user.id,
        invoice_number=payload.invoice_number,
        reason=payload.reason,
        supplier_id=payload.supplier_id,
    )
    logs_service.record(
        db, current_user.id, "stock_movement_created",
        {"movement_id": movement.id, "type": movement.type.value, "qty_units": movement.qty_units},
        client_ip(request),
    )
    return movement


@router.post("/movements/{movement_id}/validate", response_model=StockMovementOut)
def validate_movement(
    movement_id: int,
    payload: StockMovementValidate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.MANAGER)),
):
    movement = db.get(StockMovement, movement_id)
    if not movement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mouvement introuvable")

    try:
        movement = stock_service.validate_movement(db, movement, current_user, payload.approve, payload.comment)
    except stock_service.SelfValidationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except stock_service.ValidatorRoleError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except stock_service.MovementAlreadyProcessedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    logs_service.record(
        db, current_user.id, "stock_movement_validated",
        {"movement_id": movement.id, "approved": payload.approve}, client_ip(request),
    )
    return movement


@router.get("/movements/pending", response_model=list[StockMovementOut])
def list_pending(db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN, Role.MANAGER))):
    from app.models import MovementStatus

    return db.query(StockMovement).filter(StockMovement.status == MovementStatus.PENDING).all()


@router.get("/alerts", response_model=list[ProductOut])
def stock_alerts(db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN, Role.MANAGER, Role.CAISSIER))):
    products = db.query(Product).filter(Product.is_active.is_(True)).all()
    alerted = [p for p in products if products_service.is_below_alert_threshold(db, p)]
    result = []
    for p in alerted:
        out = ProductOut.model_validate(p)
        out.current_stock_units = products_service.get_current_stock_units(db, p.id)
        result.append(out)
    return result
