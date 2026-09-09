from sqlalchemy.orm import Session

from app.models import Customer


class InsufficientCreditError(Exception):
    pass


def find_or_create_customer(db: Session, name: str, phone: str | None) -> Customer:
    if phone:
        existing = db.query(Customer).filter(Customer.phone == phone).first()
        if existing:
            return existing

    customer = Customer(name=name, phone=phone, credit_balance_gnf=0)
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
