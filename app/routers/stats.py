import json
from datetime import date

from sqlalchemy import func
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import Log, Product, Quote, Role, Sale, SaleItem, SaleStatus, StockMovement, User
from app.services import predictions as predictions_service

router = APIRouter(prefix="/api/stats", tags=["stats"])

# Types de mouvements affichés dans le flux d'activité du jour, avec leur
# libellé français construit à partir des détails JSON enregistrés par
# logs_service.record(...) au moment de l'action.
TODAY_ACTIVITY_LABELS = {
    "sale_created": lambda d: f"Vente #{d.get('sale_id')} enregistrée ({int(d.get('total', 0)):,} GNF)".replace(",", " "),
    "sale_cancelled": lambda d: f"Vente #{d.get('sale_id')} annulée ({d.get('reason', '')})",
    "return_created": lambda d: f"Retour enregistré (vente #{d.get('sale_id')}) : {int(d.get('refund', 0)):,} GNF crédités".replace(",", " "),
    "quote_created": lambda d: f"Devis #{d.get('quote_id')} créé ({int(d.get('total', 0)):,} GNF)".replace(",", " "),
    "quote_converted": lambda d: f"Devis #{d.get('quote_id')} converti en vente #{d.get('sale_id')}",
    "quote_cancelled": lambda d: f"Devis #{d.get('quote_id')} annulé",
    "stock_movement_created": lambda d: f"Mouvement de stock #{d.get('movement_id')} saisi ({d.get('type')}, {d.get('qty_units')} unités)",
    "stock_movement_validated": lambda d: f"Mouvement de stock #{d.get('movement_id')} {'validé' if d.get('approved') else 'rejeté'}",
    "cash_session_opened": lambda d: f"Session de caisse #{d.get('session_id')} ouverte",
    "cash_session_closed": lambda d: f"Session de caisse #{d.get('session_id')} fermée",
    "cash_session_blocked": lambda d: f"⚠️ Session de caisse #{d.get('session_id')} BLOQUÉE (écart {int(d.get('gap', 0)):,} GNF)".replace(",", " "),
    "cash_session_resolved": lambda d: f"Session de caisse #{d.get('session_id')} résolue ({d.get('comment', '')})",
    "debt_repaid": lambda d: f"Règlement de créance : {int(d.get('amount', 0)):,} GNF (client #{d.get('customer_id')})".replace(",", " "),
    "credit_limit_exceeded": lambda d: f"⚠️ Vente à crédit refusée : limite de créances atteinte ({d.get('customer_name') or 'client #' + str(d.get('customer_id'))})",
}


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


@router.get("/expiry-alerts")
def expiry_alerts(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN, Role.MANAGER)),
):
    products = db.query(Product).filter(Product.is_active.is_(True)).all()
    alerts = []
    for p in products:
        alerts.extend(predictions_service.expiring_batches(db, p, settings.EXPIRY_ALERT_DAYS))
    return alerts


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


@router.get("/today-summary")
def today_summary(db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN, Role.MANAGER))):
    today = date.today()

    revenue_gnf = db.query(func.coalesce(func.sum(Sale.total_amount), 0)).filter(
        Sale.status == SaleStatus.VALIDE, func.date(Sale.created_at) == today
    ).scalar()
    sales_count = db.query(func.count(Sale.id)).filter(
        Sale.status == SaleStatus.VALIDE, func.date(Sale.created_at) == today
    ).scalar()
    quotes_created_count = db.query(func.count(Quote.id)).filter(func.date(Quote.created_at) == today).scalar()
    quotes_converted_count = db.query(func.count(Quote.id)).filter(func.date(Quote.converted_at) == today).scalar()
    stock_movements_count = db.query(func.count(StockMovement.id)).filter(
        func.date(StockMovement.created_at) == today
    ).scalar()
    cash_gap_alerts_count = db.query(func.count(Log.id)).filter(
        Log.action == "cash_session_blocked", func.date(Log.created_at) == today
    ).scalar()

    return {
        "revenue_gnf": int(revenue_gnf or 0),
        "sales_count": int(sales_count or 0),
        "quotes_created_count": int(quotes_created_count or 0),
        "quotes_converted_count": int(quotes_converted_count or 0),
        "stock_movements_count": int(stock_movements_count or 0),
        "cash_gap_alerts_count": int(cash_gap_alerts_count or 0),
    }


@router.get("/today-products")
def today_products(db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN, Role.MANAGER))):
    today = date.today()
    rows = (
        db.query(Product.name, func.sum(SaleItem.qty_units).label("qty_sold"))
        .join(SaleItem, SaleItem.product_id == Product.id)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .filter(Sale.status == SaleStatus.VALIDE, func.date(Sale.created_at) == today)
        .group_by(Product.name)
        .order_by(func.sum(SaleItem.qty_units).desc())
        .all()
    )
    return [{"name": name, "qty_sold": int(qty_sold)} for name, qty_sold in rows]


@router.get("/today-activity")
def today_activity(db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN, Role.MANAGER))):
    today = date.today()
    logs = (
        db.query(Log)
        .filter(func.date(Log.created_at) == today, Log.action.in_(TODAY_ACTIVITY_LABELS.keys()))
        .order_by(Log.created_at.desc())
        .limit(200)
        .all()
    )

    items = []
    for log in logs:
        details = json.loads(log.details) if log.details else {}
        user = db.get(User, log.user_id) if log.user_id else None
        actor = (user.full_name or user.username) if user else "Système"
        label = TODAY_ACTIVITY_LABELS[log.action](details)
        items.append({"id": log.id, "created_at": log.created_at, "actor": actor, "action": log.action, "label": label})

    return items
