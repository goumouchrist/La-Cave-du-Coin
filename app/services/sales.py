from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import CashSession, CashSessionStatus, Customer, MovementType, PaymentMode, Product, Role, Sale, SaleItem, SaleStatus, User
from app.services import customers as customers_service
from app.services.products import get_current_stock_units
from app.services.stock import create_movement
from app.utils import generate_transaction_number, round_gnf, to_aware_utc


class CashSessionClosedError(Exception):
    pass


class CustomerRequiredError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class QuantityConfirmationRequiredError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


class CancelNotAllowedError(Exception):
    pass


class AlreadyCancelledError(Exception):
    pass


def create_sale(
    db: Session,
    cashier: User,
    cash_session_id: int,
    payment_mode,
    amount_given: int,
    items: list[dict],
    customer_id: int | None = None,
) -> Sale:
    session_ = db.get(CashSession, cash_session_id)
    if session_ is None or session_.status != CashSessionStatus.OPEN:
        raise CashSessionClosedError("La session de caisse n'est pas ouverte")

    customer = None
    if payment_mode == PaymentMode.AVOIR:
        if not customer_id:
            raise CustomerRequiredError("Le paiement par avoir nécessite de sélectionner le client")
        customer = db.get(Customer, customer_id)
        if customer is None:
            raise CustomerRequiredError(f"Client introuvable (id={customer_id})")

    sale_items: list[SaleItem] = []
    total = 0

    for item in items:
        product = db.get(Product, item["product_id"])
        if product is None or not product.is_active:
            raise ProductNotFoundError(f"Produit inconnu (id={item['product_id']})")

        qty = item["qty"]

        if qty > settings.IDENTICAL_ITEMS_CONFIRM_THRESHOLD and not item.get("quantity_confirmed"):
            raise QuantityConfirmationRequiredError(
                f"Vente de {qty} x '{product.name}' (> {settings.IDENTICAL_ITEMS_CONFIRM_THRESHOLD}) : "
                "confirmation de quantité requise (double scan / bouton confirmer)."
            )

        available = get_current_stock_units(db, product.id)
        if available < qty:
            raise InsufficientStockError(f"Stock insuffisant pour '{product.name}' (disponible: {available}, demandé: {qty})")

        line_total = product.prix_vente * qty
        total += line_total

        sale_items.append(
            SaleItem(
                product_id=product.id,
                qty_units=qty,
                unit_price=product.prix_vente,
                quantity_confirmed=item.get("quantity_confirmed", False),
            )
        )

    if payment_mode == PaymentMode.AVOIR:
        customers_service.debit_account(db, customer, total)
        amount_given = total
        change = 0
    else:
        change = round_gnf(max(amount_given - total, 0))

    sale = Sale(
        transaction_number=generate_transaction_number(),
        cash_session_id=cash_session_id,
        cashier_id=cashier.id,
        payment_mode=payment_mode,
        customer_id=customer.id if customer else None,
        total_amount=total,
        amount_given=amount_given,
        change_amount=change,
        status=SaleStatus.VALIDE,
    )
    sale.items = sale_items
    db.add(sale)
    db.commit()
    db.refresh(sale)

    for item in sale_items:
        product = db.get(Product, item.product_id)
        create_movement(
            db,
            product,
            MovementType.SORTIE_VENTE,
            item.qty_units,
            unit="unite",
            created_by=cashier.id,
            reason=f"Vente {sale.transaction_number}",
        )

    return sale


def cancel_sale(db: Session, sale: Sale, canceller: User, reason: str) -> Sale:
    if sale.status == SaleStatus.ANNULEE:
        raise AlreadyCancelledError("Ce ticket est déjà annulé")

    if canceller.role not in (Role.MANAGER, Role.ADMIN, Role.SUPER_ADMIN):
        elapsed = datetime.now(timezone.utc) - to_aware_utc(sale.created_at)
        if elapsed > timedelta(minutes=settings.CANCEL_WINDOW_MINUTES):
            raise CancelNotAllowedError(
                f"Un caissier ne peut annuler un ticket que dans les {settings.CANCEL_WINDOW_MINUTES} minutes suivant la vente"
            )
        if not reason:
            raise CancelNotAllowedError("Un motif est obligatoire pour annuler un ticket")

    sale.status = SaleStatus.ANNULEE
    sale.cancelled_by = canceller.id
    sale.cancel_reason = reason
    sale.cancelled_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sale)
    return sale


def register_print(db: Session, sale: Sale) -> bool:
    """Incrémente le compteur d'impression. Renvoie True si c'est un DUPLICATA (2e impression ou plus)."""
    sale.print_count += 1
    db.commit()
    return sale.print_count > 1
