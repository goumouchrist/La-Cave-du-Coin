from sqlalchemy.orm import Session

from app.models import Customer, CustomerRepayment, PaymentMode, Sale


class InsufficientCreditError(Exception):
    pass


def find_or_create_customer(db: Session, name: str, phone: str | None, address: str | None = None) -> Customer:
    if phone:
        existing = db.query(Customer).filter(Customer.phone == phone).first()
        if existing:
            if address and not existing.address:
                existing.address = address
                db.commit()
                db.refresh(existing)
            return existing

    customer = Customer(name=name, phone=phone, address=address, credit_balance_gnf=0)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def credit_account(db: Session, customer: Customer, amount: int) -> Customer:
    customer.credit_balance_gnf += amount
    db.commit()
    db.refresh(customer)
    return customer


def debit_account(db: Session, customer: Customer, amount: int) -> Customer:
    if customer.credit_balance_gnf < amount:
        raise InsufficientCreditError(
            f"Solde avoir insuffisant pour {customer.name} (solde: {customer.credit_balance_gnf} GNF, requis: {amount} GNF)"
        )
    customer.credit_balance_gnf -= amount
    db.commit()
    db.refresh(customer)
    return customer


def record_debt(db: Session, customer: Customer, amount: int) -> Customer:
    """Enregistre une dette (vente à crédit non intégralement payée) :
    contrairement à debit_account, autorise le solde à devenir négatif
    (le client doit désormais cette somme à la boutique)."""
    customer.credit_balance_gnf -= amount
    db.commit()
    db.refresh(customer)
    return customer


def record_repayment(
    db: Session, customer: Customer, amount: int, processed_by: int, payment_mode: PaymentMode | None = None
) -> CustomerRepayment:
    """Règlement (partiel ou total) d'une créance : crédite le solde, répartit
    le montant sur les ventes à crédit encore dues (de la plus ancienne
    échéance à la plus récente) et garde une trace persistante (qui, quand,
    combien, par quel moyen) pour l'audit et le reçu."""
    credit_account(db, customer, amount)
    _allocate_repayment_to_sales(db, customer, amount)
    repayment = CustomerRepayment(
        customer_id=customer.id, amount_gnf=amount, processed_by=processed_by, payment_mode=payment_mode
    )
    db.add(repayment)
    db.commit()
    db.refresh(repayment)
    return repayment


def _allocate_repayment_to_sales(db: Session, customer: Customer, amount: int) -> None:
    remaining = amount
    due_sales = (
        db.query(Sale)
        .filter(Sale.customer_id == customer.id, Sale.remaining_due_gnf > 0)
        .order_by(Sale.due_date.asc().nullslast(), Sale.created_at.asc())
        .all()
    )
    for sale in due_sales:
        if remaining <= 0:
            break
        applied = min(sale.remaining_due_gnf, remaining)
        sale.remaining_due_gnf -= applied
        remaining -= applied
    db.commit()


def count_active_credits(db: Session, customer: Customer) -> int:
    """Nombre de ventes à crédit encore (partiellement) impayées pour ce
    client : retombe naturellement à 0 dès que tout est réglé, grâce à
    _allocate_repayment_to_sales qui met à jour remaining_due_gnf par vente."""
    return db.query(Sale).filter(Sale.customer_id == customer.id, Sale.remaining_due_gnf > 0).count()


def list_customers_with_debt(db: Session) -> list[dict]:
    """Clients ayant un solde négatif (dette), avec la date de leur vente à
    crédit la plus ancienne encore due et la plus récente, pour prioriser les
    relances (plus la dette est ancienne, plus c'est urgent)."""
    customers = (
        db.query(Customer)
        .filter(Customer.credit_balance_gnf < 0)
        .order_by(Customer.credit_balance_gnf.asc())
        .all()
    )

    result = []
    for customer in customers:
        due_sales = (
            db.query(Sale)
            .filter(Sale.customer_id == customer.id, Sale.remaining_due_gnf > 0)
            .order_by(Sale.due_date.asc().nullslast())
            .all()
        )
        oldest_due_date = due_sales[0].due_date if due_sales else None
        most_recent_sale_at = max((s.created_at for s in due_sales), default=None)
        result.append(
            {
                "customer": customer,
                "amount_owed_gnf": -customer.credit_balance_gnf,
                "oldest_due_date": oldest_due_date,
                "most_recent_sale_at": most_recent_sale_at,
            }
        )
    return result
