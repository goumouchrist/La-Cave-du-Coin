from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Customer
from app.schemas import CustomerOut, DebtOut, DebtRepayment
from app.services import customers as customers_service

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("/search", response_model=list[CustomerOut])
def search_customers(phone: str | None = None, name: str | None = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    query = db.query(Customer)
    if phone:
        query = query.filter(Customer.phone == phone)
    if name:
        query = query.filter(Customer.name.ilike(f"%{name}%"))
    return query.limit(20).all()


@router.get("/debts", response_model=list[DebtOut])
def list_debts(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return customers_service.list_customers_with_debt(db)


@router.post("/{customer_id}/repay-debt", response_model=CustomerOut)
def repay_debt(customer_id: int, payload: DebtRepayment, db: Session = Depends(get_db), _=Depends(get_current_user)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
    return customers_service.credit_account(db, customer, payload.amount)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
    return customer
