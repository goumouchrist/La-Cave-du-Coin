from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Product, Quote, QuoteItem, QuoteStatus, Sale, User
from app.services import sales as sales_service
from app.utils import generate_quote_number


class ProductNotFoundError(Exception):
    pass


class QuoteNotConvertibleError(Exception):
    pass


def create_quote(
    db: Session,
    creator: User,
    items: list[dict],
    customer_id: int | None = None,
    customer_name: str | None = None,
    customer_phone: str | None = None,
    validity_days: int | None = None,
) -> Quote:
    quote_items: list[QuoteItem] = []
    total = 0

    for item in items:
        product = db.get(Product, item["product_id"])
        if product is None or not product.is_active:
            raise ProductNotFoundError(f"Produit inconnu (id={item['product_id']})")

        qty = item["qty"]
        line_total = product.prix_vente * qty
        total += line_total

        quote_items.append(
            QuoteItem(product_id=product.id, qty_units=qty, unit_price=product.prix_vente)
        )

    days = validity_days if validity_days is not None else settings.QUOTE_VALIDITY_DAYS
    expires_at = date.today() + timedelta(days=days) if days else None

    quote = Quote(
        quote_number=generate_quote_number(),
        created_by=creator.id,
        customer_id=customer_id,
        customer_name=customer_name,
        customer_phone=customer_phone,
        total_amount=total,
        status=QuoteStatus.EN_COURS,
        expires_at=expires_at,
    )
    quote.items = quote_items
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


def _effective_status(quote: Quote) -> QuoteStatus:
    """Un devis EN_COURS dont la date d'expiration est dépassée est traité comme
    EXPIRE au moment de la lecture/conversion, sans tâche cron : le statut stocké
    n'est mis à jour en base que lors d'une tentative de conversion."""
    if quote.status == QuoteStatus.EN_COURS and quote.expires_at and date.today() > quote.expires_at:
        return QuoteStatus.EXPIRE
    return quote.status


def convert_to_sale(
    db: Session,
    quote: Quote,
    cashier: User,
    cash_session_id: int,
    payment_mode,
    amount_given: int,
    customer_id: int | None = None,
    customer_name: str | None = None,
    customer_phone: str | None = None,
    customer_address: str | None = None,
    customer_email: str | None = None,
    due_date: date | None = None,
) -> Sale:
    effective = _effective_status(quote)
    if effective != QuoteStatus.EN_COURS:
        if effective == QuoteStatus.EXPIRE and quote.status == QuoteStatus.EN_COURS:
            quote.status = QuoteStatus.EXPIRE
            db.commit()
        raise QuoteNotConvertibleError(f"Ce devis n'est plus convertible (statut: {effective.value})")

    items = [
        {
            "product_id": qi.product_id,
            "qty": qi.qty_units,
            "quantity_confirmed": True,
            "unit_price_override": qi.unit_price,
        }
        for qi in quote.items
    ]

    sale = sales_service.create_sale(
        db,
        cashier,
        cash_session_id,
        payment_mode,
        amount_given,
        items,
        customer_id=customer_id if customer_id is not None else quote.customer_id,
        customer_name=customer_name or quote.customer_name,
        customer_phone=customer_phone or quote.customer_phone,
        customer_address=customer_address,
        customer_email=customer_email,
        due_date=due_date,
    )

    quote.status = QuoteStatus.CONVERTI
    quote.converted_sale_id = sale.id
    quote.converted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(quote)
    return sale


def cancel_quote(db: Session, quote: Quote) -> Quote:
    if quote.status != QuoteStatus.EN_COURS:
        raise QuoteNotConvertibleError(f"Ce devis ne peut pas être annulé (statut: {quote.status.value})")

    quote.status = QuoteStatus.ANNULE
    quote.cancelled_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(quote)
    return quote


def register_print(db: Session, quote: Quote) -> bool:
    """Incrémente le compteur d'impression. Renvoie True si c'est un DUPLICATA (2e impression ou plus)."""
    quote.print_count += 1
    db.commit()
    return quote.print_count > 1
