from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import client_ip, get_current_user
from app.models import Product, Sale, User
from app.schemas import ReturnCreate, ReturnOut, SaleCancel, SaleCreate, SaleOut, ScanRequest
from app.services import customers as customers_service
from app.services import logs as logs_service
from app.services import products as products_service
from app.services import receipts as receipts_service
from app.services import returns as returns_service
from app.services import sales as sales_service
from app.services import scan as scan_service

router = APIRouter(prefix="/api/sales", tags=["sales"])

SALES_SERVICE_ERRORS = (
    sales_service.CashSessionClosedError,
    sales_service.InsufficientStockError,
    sales_service.QuantityConfirmationRequiredError,
    sales_service.ProductNotFoundError,
    sales_service.CustomerRequiredError,
    customers_service.InsufficientCreditError,
)

RETURN_SERVICE_ERRORS = (
    returns_service.SaleNotEligibleError,
    returns_service.ReturnQuantityExceededError,
    returns_service.SaleItemNotFoundError,
)


@router.post("", response_model=SaleOut, status_code=status.HTTP_201_CREATED)
def create_sale(payload: SaleCreate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        sale = sales_service.create_sale(
            db,
            current_user,
            payload.cash_session_id,
            payload.payment_mode,
            payload.amount_given,
            [item.model_dump() for item in payload.items],
            customer_id=payload.customer_id,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            customer_address=payload.customer_address,
            due_date=payload.due_date,
        )
    except SALES_SERVICE_ERRORS as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    logs_service.record(db, current_user.id, "sale_created", {"sale_id": sale.id, "total": sale.total_amount}, client_ip(request))
    return sale


@router.get("/by-transaction/{transaction_number}", response_model=SaleOut)
def get_sale_by_transaction(transaction_number: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    sale = db.query(Sale).filter(Sale.transaction_number == transaction_number).first()
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aucune vente avec ce numéro de transaction")
    return sale


@router.get("/{sale_id}", response_model=SaleOut)
def get_sale(sale_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    sale = db.get(Sale, sale_id)
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vente introuvable")
    return sale


@router.post("/{sale_id}/cancel", response_model=SaleOut)
def cancel_sale(sale_id: int, payload: SaleCancel, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sale = db.get(Sale, sale_id)
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vente introuvable")

    try:
        sale = sales_service.cancel_sale(db, sale, current_user, payload.reason)
    except sales_service.CancelNotAllowedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except sales_service.AlreadyCancelledError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    logs_service.record(db, current_user.id, "sale_cancelled", {"sale_id": sale.id, "reason": payload.reason}, client_ip(request))
    return sale


@router.get("/{sale_id}/receipt.pdf")
def get_receipt(sale_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sale = db.get(Sale, sale_id)
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vente introuvable")

    is_duplicata = sales_service.register_print(db, sale)
    products_by_id = {item.product_id: db.get(Product, item.product_id) for item in sale.items}
    cashier = db.get(User, sale.cashier_id)
    cashier_name = (cashier.full_name or cashier.username) if cashier else ""

    pdf_bytes = receipts_service.build_receipt_pdf(sale, products_by_id, cashier_name, is_duplicata)

    logs_service.record(
        db, current_user.id, "receipt_printed",
        {"sale_id": sale.id, "print_count": sale.print_count, "duplicata": is_duplicata}, client_ip(request),
    )
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.post("/{sale_id}/return", response_model=ReturnOut, status_code=status.HTTP_201_CREATED)
def create_return(sale_id: int, payload: ReturnCreate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sale = db.get(Sale, sale_id)
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vente introuvable")

    try:
        return_ = returns_service.create_return(
            db,
            sale,
            [item.model_dump() for item in payload.items],
            payload.customer_name,
            payload.customer_phone,
            current_user,
            payload.reason,
        )
    except RETURN_SERVICE_ERRORS as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    logs_service.record(
        db, current_user.id, "return_created",
        {"return_id": return_.id, "sale_id": sale.id, "refund": return_.total_refund_gnf}, client_ip(request),
    )
    return return_


@router.post("/scan")
def scan_barcode(payload: ScanRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    product = products_service.find_by_barcode(db, payload.barcode)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produit inconnu")

    _, is_double_scan = scan_service.log_scan(db, current_user.id, product, payload.action_type)
    return {
        "product_id": product.id,
        "name": product.name,
        "prix_vente": product.prix_vente,
        "double_scan_alert": is_double_scan,
    }
