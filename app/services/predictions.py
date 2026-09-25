from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import MovementStatus, MovementType, Product, Sale, SaleItem, SaleStatus, StockMovement
from app.services.products import get_batches_remaining, get_current_stock_units


def top_selling_products(db: Session, days: int = 7, limit: int = 5) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.query(SaleItem.product_id, func.sum(SaleItem.qty_units).label("total_qty"))
        .join(Sale, Sale.id == SaleItem.sale_id)
        .filter(Sale.created_at >= since, Sale.status == SaleStatus.VALIDE)
        .group_by(SaleItem.product_id)
        .order_by(func.sum(SaleItem.qty_units).desc())
        .limit(limit)
        .all()
    )
    result = []
    for product_id, total_qty in rows:
        product = db.get(Product, product_id)
        result.append({"product_id": product_id, "name": product.name if product else "?", "qty_sold": int(total_qty)})
    return result


def stockout_forecast(db: Session, product: Product, lookback_days: int = 30) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    consumed = (
        db.query(func.coalesce(func.sum(StockMovement.qty_units), 0))
        .filter(
            StockMovement.product_id == product.id,
            StockMovement.type == MovementType.SORTIE_VENTE,
            StockMovement.status == MovementStatus.VALIDATED,
            StockMovement.created_at >= since,
        )
        .scalar()
    )
    avg_daily = int(consumed) / lookback_days
    current_stock = get_current_stock_units(db, product.id)

    if avg_daily <= 0:
        return {"product_id": product.id, "name": product.name, "avg_daily_consumption": 0.0, "days_remaining": None, "alert": False}

    days_remaining = current_stock / avg_daily
    return {
        "product_id": product.id,
        "name": product.name,
        "avg_daily_consumption": round(avg_daily, 2),
        "days_remaining": round(days_remaining, 1),
        "alert": days_remaining < 3,
    }


def expiring_batches(db: Session, product: Product, within_days: int) -> list[dict]:
    cutoff = date.today() + timedelta(days=within_days)
    batches = get_batches_remaining(db, product.id)
    return [
        {
            "product_id": product.id,
            "name": product.name,
            "movement_id": b["movement_id"],
            "expiry_date": b["expiry_date"],
            "remaining_units": b["remaining_units"],
            "days_left": (b["expiry_date"] - date.today()).days,
        }
        for b in batches
        if b["expiry_date"] is not None and b["remaining_units"] > 0 and b["expiry_date"] <= cutoff
    ]


def _linear_regression(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Régression linéaire simple (moindres carrés) : renvoie (pente, intercept)."""
    n = len(xs)
    if n < 2:
        return 0.0, ys[0] if ys else 0.0

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator = sum((x - mean_x) ** 2 for x in xs)

    if denominator == 0:
        return 0.0, mean_y

    slope = numerator / denominator
    intercept = mean_y - slope * mean_x
    return slope, intercept


def forecast_next_day_revenue(db: Session, history_days: int = 30) -> dict:
    since = (datetime.now(timezone.utc) - timedelta(days=history_days)).date()
    rows = (
        db.query(func.date(Sale.created_at).label("day"), func.sum(Sale.total_amount).label("total"))
        .filter(Sale.created_at >= since, Sale.status == SaleStatus.VALIDE)
        .group_by(func.date(Sale.created_at))
        .order_by(func.date(Sale.created_at))
        .all()
    )

    if not rows:
        return {"predicted_revenue_gnf": 0, "based_on_days": 0}

    xs = list(range(len(rows)))
    ys = [float(total) for _, total in rows]
    slope, intercept = _linear_regression(xs, ys)
    next_x = len(rows)
    predicted = max(slope * next_x + intercept, 0)

    return {"predicted_revenue_gnf": round(predicted), "based_on_days": len(rows)}
