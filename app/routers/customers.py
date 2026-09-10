from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import client_ip, get_current_user
from app.models import Customer, CustomerRepayment, User
from app.schemas import CustomerOut, DebtOut, DebtRepayment, RepaymentOut
from app.services import customers as customers_service
from app.services import logs as logs_service
from app.services import receipts as receipts_service

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


@router.post("/{customer_id}/repay-debt", response_model=RepaymentOut, status_code=status.HTTP_201_CREATED)
def repay_debt(customer_id: int, payload: DebtRepayment, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")

    repayment = customers_service.record_repayment(db, customer, payload.amount, current_user.id)

    logs_service.record(
        db, current_user.id, "debt_repaid",
        {"customer_id": customer.id, "amount": payload.amount, "repayment_id": repayment.id}, client_ip(request),
    )
    return repayment


@router.get("/repayments/{repayment_id}/receipt.pdf")
def get_repayment_receipt(repayment_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    repayment = db.get(CustomerRepayment, repayment_id)
    if not repayment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Règlement introuvable")

    processor = db.get(User, repayment.processed_by)
    processor_name = (processor.full_name or processor.username) if processor else ""

    pdf_bytes = receipts_service.build_repayment_receipt_pdf(repayment, processor_name)
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
    return customer
