from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    CashSession,
    CashSessionStatus,
    MovementType,
    PaymentMode,
    Product,
    Return,
    ReturnItem,
    Role,
    Sale,
    SaleItem,
    SaleStatus,
    User,
)
from app.services import customers as customers_service
from app.services.stock import create_movement

MANAGER_TIER_ROLES = (Role.MANAGER, Role.ADMIN, Role.SUPER_ADMIN)


class SaleNotEligibleError(Exception):
    pass


class ReturnQuantityExceededError(Exception):
    pass


class SaleItemNotFoundError(Exception):
    pass


class NoOpenCashSessionError(Exception):
    pass


class CashRefundRequiresManagerError(Exception):
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
    refund_mode: PaymentMode = PaymentMode.AVOIR,
) -> Return:
    if sale.status != SaleStatus.VALIDE:
        raise SaleNotEligibleError("Seule une vente valide peut faire l'objet d'un retour")

    cash_session = None
    if refund_mode == PaymentMode.ESPECES:
        cash_session = db.query(CashSession).filter(CashSession.status == CashSessionStatus.OPEN).first()
        if cash_session is None:
            raise NoOpenCashSessionError(
                "Aucune session de caisse ouverte : impossible de rembourser en espèces "
                "(choisissez l'avoir, ou ouvrez d'abord une session de caisse)"
            )

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

    if (
        refund_mode == PaymentMode.ESPECES
        and total_refund > settings.RETURN_CASH_REFUND_MANAGER_THRESHOLD_GNF
        and processed_by.role not in MANAGER_TIER_ROLES
    ):
        raise CashRefundRequiresManagerError(
            f"Un remboursement en espèces de {total_refund} GNF dépasse le seuil autorisé pour un "
            f"caissier ({settings.RETURN_CASH_REFUND_MANAGER_THRESHOLD_GNF} GNF) : un Manager ou "
            "Admin doit le traiter lui-même"
        )

    return_ = Return(
        sale_id=sale.id,
        customer_id=customer.id,
        processed_by=processed_by.id,
        reason=reason,
        total_refund_gnf=total_refund,
        refund_mode=refund_mode,
        cash_session_id=cash_session.id if cash_session else None,
    )
    return_.items = return_items
    db.add(return_)
    db.commit()
    db.refresh(return_)

    # Le produit revient physiquement en stock quel que soit le mode de
    # remboursement choisi (avoir ou espèces) : seule la contrepartie
    # financière change, jamais le mouvement de stock lui-même.
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

    if refund_mode == PaymentMode.AVOIR:
        customers_service.credit_account(db, customer, total_refund)
    # En espèces : pas de crédit d'avoir, l'argent est rendu physiquement et le
    # rattachement à cash_session_id (ci-dessus) suffit à ce que
    # compute_theoretical_amount le soustraie du montant théorique attendu.

    return return_
