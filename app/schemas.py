from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models import CashSessionStatus, MovementStatus, MovementType, PaymentMode, Role, SaleStatus


# ---------- Auth / Users ----------

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role
    user_id: int
    username: str


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str = ""
    role: Role


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: Role
    is_active: bool

    class Config:
        from_attributes = True


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=6)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class UserStatusUpdate(BaseModel):
    is_active: bool


# ---------- Products ----------

class ProductCreate(BaseModel):
    name: str
    category: str
    barcode: str | None = None
    supplier_id: int | None = None
    unit_carton_qty: int = 24
    unit_pack_qty: int = 6
    prix_achat: int = Field(ge=0)
    prix_vente: int = Field(ge=0)
    tva_rate: float = 0.0
    stock_min_cartons: int = 5


class ProductUpdatePrice(BaseModel):
    prix_achat: int | None = Field(default=None, ge=0)
    prix_vente: int | None = Field(default=None, ge=0)
    tva_rate: float | None = Field(default=None, ge=0, le=1)
    is_promo: bool = False


class ProductImportResult(BaseModel):
    created: list[str]
    errors: list[dict]


class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    barcode: str | None
    supplier_id: int | None
    unit_carton_qty: int
    unit_pack_qty: int
    prix_achat: int
    prix_vente: int
    tva_rate: float
    stock_min_cartons: int
    is_active: bool
    current_stock_units: int = 0

    class Config:
        from_attributes = True


# ---------- Suppliers ----------

class SupplierCreate(BaseModel):
    name: str
    phone: str | None = None
    address: str | None = None


class SupplierOut(BaseModel):
    id: int
    name: str
    phone: str | None
    address: str | None
    is_active: bool

    class Config:
        from_attributes = True


# ---------- Stock ----------

class StockMovementCreate(BaseModel):
    product_id: int
    type: MovementType
    qty: int = Field(gt=0, description="Quantité exprimée dans l'unité fournie")
    unit: str = Field(default="unite", description="unite | carton | pack")
    invoice_number: str | None = None
    reason: str | None = None
    supplier_id: int | None = None


class StockMovementValidate(BaseModel):
    approve: bool
    comment: str | None = None


class StockMovementOut(BaseModel):
    id: int
    product_id: int
    supplier_id: int | None
    type: MovementType
    qty_units: int
    invoice_number: str | None
    reason: str | None
    status: MovementStatus
    created_by: int
    validated_by: int | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Cash sessions ----------

class CashSessionOpen(BaseModel):
    opening_amount: int = Field(ge=0)


class CashSessionClose(BaseModel):
    closing_physical: int = Field(ge=0)


class CashSessionOut(BaseModel):
    id: int
    opened_by: int
    closed_by: int | None
    opening_amount: int
    closing_theoretical: int | None
    closing_physical: int | None
    gap_amount: int | None
    status: CashSessionStatus
    opened_at: datetime
    closed_at: datetime | None
    resolved_by: int | None
    resolved_at: datetime | None
    resolution_comment: str | None

    class Config:
        from_attributes = True


class CashSessionResolve(BaseModel):
    comment: str = Field(min_length=3)


class CashSessionSummary(BaseModel):
    session_id: int
    opening_amount: int
    theoretical_cash: int
    by_payment_mode: dict[str, int]
    sales_count: int


class CashMovementOut(BaseModel):
    sale_id: int
    transaction_number: str
    cashier_id: int
    amount: int
    running_total: int
    created_at: datetime


# ---------- Sales ----------

class SaleItemIn(BaseModel):
    product_id: int
    qty: int = Field(gt=0)
    quantity_confirmed: bool = False


class SaleCreate(BaseModel):
    cash_session_id: int
    payment_mode: PaymentMode
    amount_given: int = Field(ge=0)
    items: list[SaleItemIn]
    customer_id: int | None = Field(default=None, description="Requis si payment_mode = avoir, ou pour un client crédit déjà connu")
    customer_name: str | None = Field(default=None, description="Nouveau client crédit (si customer_id non fourni)")
    customer_phone: str | None = None
    customer_address: str | None = None
    customer_email: str | None = Field(default=None, description="Pour l'envoi du reçu par email (facultatif, toute vente)")
    due_date: date | None = Field(default=None, description="Date de remboursement prévue (mode crédit)")


class SaleItemOut(BaseModel):
    id: int
    product_id: int
    qty_units: int
    unit_price: int
    quantity_confirmed: bool

    class Config:
        from_attributes = True


class SaleOut(BaseModel):
    id: int
    transaction_number: str
    cash_session_id: int
    cashier_id: int
    payment_mode: PaymentMode
    customer_id: int | None
    total_amount: int
    amount_given: int
    change_amount: int
    remaining_due_gnf: int
    due_date: date | None
    status: SaleStatus
    print_count: int
    customer_email: str | None
    receipt_email_sent_at: datetime | None
    created_at: datetime
    items: list[SaleItemOut]

    class Config:
        from_attributes = True


class SaleEmailRequest(BaseModel):
    email: str | None = Field(default=None, description="Remplace l'email enregistré sur la vente, si fourni")


class SaleCancel(BaseModel):
    reason: str


# ---------- Customers & retours ----------

class CustomerOut(BaseModel):
    id: int
    name: str
    phone: str | None
    address: str | None
    credit_balance_gnf: int

    class Config:
        from_attributes = True


class DebtOut(BaseModel):
    customer: CustomerOut
    amount_owed_gnf: int
    oldest_due_date: date | None
    most_recent_sale_at: datetime | None


class DebtRepayment(BaseModel):
    amount: int = Field(gt=0)


class RepaymentOut(BaseModel):
    id: int
    customer_id: int
    amount_gnf: int
    processed_by: int
    created_at: datetime
    customer: CustomerOut

    class Config:
        from_attributes = True


class ReturnItemIn(BaseModel):
    sale_item_id: int
    qty: int = Field(gt=0)


class ReturnCreate(BaseModel):
    customer_name: str
    customer_phone: str | None = None
    items: list[ReturnItemIn]
    reason: str | None = None


class ReturnItemOut(BaseModel):
    sale_item_id: int
    product_id: int
    qty_units: int
    unit_price: int

    class Config:
        from_attributes = True


class ReturnOut(BaseModel):
    id: int
    sale_id: int
    customer_id: int
    total_refund_gnf: int
    reason: str | None
    created_at: datetime
    items: list[ReturnItemOut]

    class Config:
        from_attributes = True


# ---------- Scan ----------

class ScanRequest(BaseModel):
    barcode: str
    action_type: str = "vente"
