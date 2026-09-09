import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    ADMIN = "admin"
    CAISSIER = "caissier"
    MANAGER = "manager"


class PaymentMode(str, enum.Enum):
    ESPECES = "especes"
    MOBILE_MONEY = "mobile_money"
    CREDIT = "credit"
    AVOIR = "avoir"


class MovementType(str, enum.Enum):
    ENTREE = "entree"
    SORTIE_VENTE = "sortie_vente"
    RETOUR = "retour"
    CASSE = "casse"
    DON = "don"
    AJUSTEMENT = "ajustement"


class MovementStatus(str, enum.Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"


class CashSessionStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    BLOCKED = "blocked"


class SaleStatus(str, enum.Enum):
    VALIDE = "valide"
    ANNULEE = "annulee"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120), default="")
    role: Mapped[Role] = mapped_column(Enum(Role))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    products: Mapped[list["Product"]] = relationship(back_populates="supplier")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    barcode: Mapped[str | None] = mapped_column(String(20), unique=True, index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(150))
    category: Mapped[str] = mapped_column(String(50))
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    unit_carton_qty: Mapped[int] = mapped_column(Integer, default=24)
    unit_pack_qty: Mapped[int] = mapped_column(Integer, default=6)
    prix_achat: Mapped[int] = mapped_column(Integer)
    prix_vente: Mapped[int] = mapped_column(Integer)
    tva_rate: Mapped[float] = mapped_column(Float, default=0.0)
    stock_min_cartons: Mapped[int] = mapped_column(Integer, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    supplier: Mapped["Supplier"] = relationship(back_populates="products")
    movements: Mapped[list["StockMovement"]] = relationship(back_populates="product")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    type: Mapped[MovementType] = mapped_column(Enum(MovementType))
    qty_units: Mapped[int] = mapped_column(Integer)
    invoice_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[MovementStatus] = mapped_column(Enum(MovementStatus), default=MovementStatus.VALIDATED)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    validated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    product: Mapped["Product"] = relationship(back_populates="movements")


class CashSession(Base):
    __tablename__ = "cash_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    opened_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    closed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    opening_amount: Mapped[int] = mapped_column(Integer)
    closing_theoretical: Mapped[int | None] = mapped_column(Integer, nullable=True)
    closing_physical: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gap_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[CashSessionStatus] = mapped_column(Enum(CashSessionStatus), default=CashSessionStatus.OPEN)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sales: Mapped[list["Sale"]] = relationship(back_populates="cash_session")


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    cash_session_id: Mapped[int] = mapped_column(ForeignKey("cash_sessions.id"))
    cashier_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    payment_mode: Mapped[PaymentMode] = mapped_column(Enum(PaymentMode))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    total_amount: Mapped[int] = mapped_column(Integer)
    amount_given: Mapped[int] = mapped_column(Integer, default=0)
    change_amount: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[SaleStatus] = mapped_column(Enum(SaleStatus), default=SaleStatus.VALIDE)
    cancelled_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    print_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    cash_session: Mapped["CashSession"] = relationship(back_populates="sales")
    items: Mapped[list["SaleItem"]] = relationship(back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    qty_units: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[int] = mapped_column(Integer)
    quantity_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    sale: Mapped["Sale"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    action_type: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(30), unique=True, index=True, nullable=True)
    credit_balance_gnf: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Return(Base):
    __tablename__ = "returns"

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    processed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_refund_gnf: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    items: Mapped[list["ReturnItem"]] = relationship(back_populates="return_", cascade="all, delete-orphan")


class ReturnItem(Base):
    __tablename__ = "return_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    return_id: Mapped[int] = mapped_column(ForeignKey("returns.id"))
    sale_item_id: Mapped[int] = mapped_column(ForeignKey("sale_items.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    qty_units: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[int] = mapped_column(Integer)

    return_: Mapped["Return"] = relationship(back_populates="items")
