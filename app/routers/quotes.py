from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import client_ip, get_current_user
from app.models import Product, Quote, User
from app.schemas import QuoteConvert, QuoteCreate, QuoteOut, SaleOut
from app.services import customers as customers_service
from app.services import logs as logs_service
from app.services import quotes as quotes_service
from app.services import receipts as receipts_service
from app.services import sales as sales_service

router = APIRouter(prefix="/api/quotes", tags=["quotes"])

QUOTE_SERVICE_ERRORS = (
    quotes_service.ProductNotFoundError,
    quotes_service.QuantityConfirmationRequiredError,
    quotes_service.CustomerInfoRequiredError,
)

CONVERT_SERVICE_ERRORS = (
    sales_service.CashSessionClosedError,
    sales_service.InsufficientStockError,
    sales_service.QuantityConfirmationRequiredError,
    sales_service.ProductNotFoundError,
    sales_service.CustomerRequiredError,
    customers_service.InsufficientCreditError,
)


@router.post("", response_model=QuoteOut, status_code=status.HTTP_201_CREATED)
def create_quote(payload: QuoteCreate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        quote = quotes_service.create_quote(
            db,
            current_user,
            [item.model_dump() for item in payload.items],
            customer_id=payload.customer_id,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            validity_days=payload.validity_days,
        )
    except QUOTE_SERVICE_ERRORS as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    logs_service.record(db, current_user.id, "quote_created", {"quote_id": quote.id, "total": quote.total_amount}, client_ip(request))
    return quote


@router.get("", response_model=list[QuoteOut])
def list_quotes(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Quote).order_by(Quote.created_at.desc()).limit(200).all()


@router.get("/by-number/{quote_number}", response_model=QuoteOut)
def get_quote_by_number(quote_number: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    quote = db.query(Quote).filter(Quote.quote_number == quote_number).first()
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aucun devis avec ce numéro")
    return quote


@router.get("/{quote_id}", response_model=QuoteOut)
def get_quote(quote_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Devis introuvable")
    return quote


@router.post("/{quote_id}/convert", response_model=SaleOut, status_code=status.HTTP_201_CREATED)
def convert_quote(quote_id: int, payload: QuoteConvert, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Devis introuvable")

    try:
        sale = quotes_service.convert_to_sale(
            db,
            quote,
            current_user,
            payload.cash_session_id,
            payload.payment_mode,
            payload.amount_given,
            customer_id=payload.customer_id,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            customer_address=payload.customer_address,
            customer_email=payload.customer_email,
            due_date=payload.due_date,
        )
    except quotes_service.QuoteNotConvertibleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except CONVERT_SERVICE_ERRORS as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    logs_service.record(db, current_user.id, "quote_converted", {"quote_id": quote.id, "sale_id": sale.id}, client_ip(request))
    return sale


@router.post("/{quote_id}/cancel", response_model=QuoteOut)
def cancel_quote(quote_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Devis introuvable")

    try:
        quote = quotes_service.cancel_quote(db, quote)
    except quotes_service.QuoteNotConvertibleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    logs_service.record(db, current_user.id, "quote_cancelled", {"quote_id": quote.id}, client_ip(request))
    return quote


@router.get("/{quote_id}/pdf")
def get_quote_pdf(quote_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Devis introuvable")

    is_duplicata = quotes_service.register_print(db, quote)
    products_by_id = {item.product_id: db.get(Product, item.product_id) for item in quote.items}
    creator = db.get(User, quote.created_by)
    creator_name = (creator.full_name or creator.username) if creator else ""

    pdf_bytes = receipts_service.build_quote_pdf(quote, products_by_id, creator_name, is_duplicata)

    logs_service.record(db, current_user.id, "quote_pdf_printed", {"quote_id": quote.id}, client_ip(request))
    return Response(content=pdf_bytes, media_type="application/pdf")
