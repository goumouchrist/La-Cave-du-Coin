from sqlalchemy import func
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import Product, Role, Sale, SaleStatus, User
from app.services import predictions as predictions_service

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/top-products")
def top_products(days: int = 7, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return predictions_service.top_selling_products(db, days=days)


@router.get("/stockout-forecast")
def stockout_forecast(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN, Role.MANAGER)),
):
    products = db.query(Product).filter(Product.is_active.is_(True)).all()
    return [predictions_service.stockout_forecast(db, p) for p in products]


@router.get("/revenue-forecast")
def revenue_forecast(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN, Role.MANAGER)),
):
    return predictions_service.forecast_next_day_revenue(db)


@router.get("/sales-by-category")
def sales_by_category(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    from app.models import SaleItem

    rows = (
        db.query(Product.category, func.coalesce(func.sum(SaleItem.qty_units * SaleItem.unit_price), 0))
        .join(SaleItem, SaleItem.product_id == Product.id)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .filter(Sale.status == SaleStatus.VALIDE)
        .group_by(Product.category)
        .all()
    )
    return [{"category": category, "total_gnf": int(total)} for category, total in rows]


@router.get("/sales-by-cashier")
def sales_by_cashier(db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN, Role.MANAGER))):
    rows = (
        db.query(User.username, func.coalesce(func.sum(Sale.total_amount), 0))
        .join(Sale, Sale.cashier_id == User.id)
        .filter(Sale.status == SaleStatus.VALIDE)
        .group_by(User.username)
        .all()
    )
    return [{"cashier": username, "total_gnf": int(total)} for username, total in rows]
