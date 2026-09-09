from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import MovementType, Product, Return, ReturnItem, Sale, SaleItem, SaleStatus, User
from app.services import customers as customers_service
from app.services.stock import create_movement


class SaleNotEligibleError(Exception):
    pass


class ReturnQuantityExceededError(Exception):
    pass


class SaleItemNotFoundError(Exception):
    pass


def _already_returned_qty(db: Session, sale_item_id: int) -> int:
    total = db.query(func.coalesce(func.sum(ReturnItem.qty_units), 0)).filter(
        ReturnItem.sale_item_id == sale_item_id
    ).scalar()
    return int(total)


def create_return(
    db: Session,
    sale: Sale,
    items: list[dict],
    customer_name: str,
    customer_phone: str | None,
    processed_by: User,
    reason: str | None = None,
) -> Return:
    if sale.status != SaleStatus.VALIDE:
        raise SaleNotEligibleError("Seule une vente valide peut faire l'objet d'un retour")

    customer = customers_service.find_or_create_customer(db, customer_name, customer_phone)

    return_items: list[ReturnItem] = []
    total_refund = 0

    for entry in items:
        sale_item = db.get(SaleItem, entry["sale_item_id"])
        if sale_item is None or sale_item.sale_id != sale.id:
            raise SaleItemNotFoundError(f"Ligne de vente introuvable sur ce ticket (id={entry['sale_item_id']})")

        qty = entry["qty"]
        already_returned = _already_returned_qty(db, sale_item.id)
        if already_returned + qty > sale_item.qty_units:
            raise ReturnQuantityExceededError(
                f"Quantité de retour ({qty}) dépasse ce qui peut encore être retourné "
                f"pour cette ligne (déjà retourné: {already_returned}, vendu: {sale_item.qty_units})"
            )

        line_refund = qty * sale_item.unit_price
        total_refund += line_refund
        return_items.append(
            ReturnItem(
                sale_item_id=sale_item.id,
                product_id=sale_item.product_id,
                qty_units=qty,
                unit_price=sale_item.unit_price,
            )
        )

    return_ = Return(
        sale_id=sale.id,
        customer_id=customer.id,
        processed_by=processed_by.id,
        reason=reason,
        total_refund_gnf=total_refund,
    )
    return_.items = return_items
    db.add(return_)
    db.commit()
    db.refresh(return_)

    for item in return_items:
        product = db.get(Product, item.product_id)
        create_movement(
            db,
            product,
            MovementType.RETOUR,
            item.qty_units,
            unit="unite",
            created_by=processed_by.id,
            reason=f"Retour ticket {sale.transaction_number}" + (f" — {reason}" if reason else ""),
        )

    customers_service.credit_account(db, customer, total_refund)

    return return_
