"""Entités domaine product — aucune dépendance externe (pas de FastAPI/SQLAlchemy)."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


# ---------------------------------------------------------------------------
# Value Object — Money
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "XAF"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

    def apply_percentage_discount(self, rate: Decimal) -> "Money":
        return Money(self.amount * (1 - rate / 100), self.currency)

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add Money with different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, factor: Decimal | int) -> "Money":
        return Money(self.amount * Decimal(str(factor)), self.currency)


# ---------------------------------------------------------------------------
# Domain entities
# ---------------------------------------------------------------------------


@dataclass
class ProductCategory:
    id: int
    name: str
    slug: str
    parent_id: int | None
    image: str | None
    description: str | None
    is_active: bool
    sort_order: int
    children: list["ProductCategory"] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"ProductCategory({self.slug}: {self.name})"


@dataclass
class Brand:
    id: int
    name: str
    slug: str
    logo: str | None
    description: str | None
    is_active: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"Brand({self.slug}: {self.name})"


@dataclass
class Unit:
    id: int
    name: str
    abbreviation: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProductImage:
    id: int
    product_id: int
    image: str
    is_primary: bool
    sort_order: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProductReviewSummary:
    count: int
    average: Decimal


@dataclass
class Product:
    id: int
    vendor_id: int
    category_id: int
    brand_id: int | None
    unit_id: int | None
    name: str
    slug: str
    description: str | None
    short_description: str | None
    price: Decimal
    discount_price: Decimal | None
    stock_quantity: int
    sku: str | None
    is_active: bool
    is_featured: bool
    weight: Decimal | None
    tax_id: int | None
    # Relations dénormalisées pour la réponse
    category_name: str | None = None
    brand_name: str | None = None
    unit_name: str | None = None
    images: list[ProductImage] = field(default_factory=list)
    review_summary: ProductReviewSummary | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def effective_price(self) -> Decimal:
        """Retourne le prix effectif (réduit si applicable)."""
        if self.discount_price is not None and self.discount_price < self.price:
            return self.discount_price
        return self.price

    @property
    def is_in_stock(self) -> bool:
        return self.stock_quantity > 0

    def has_enough_stock(self, quantity: int) -> bool:
        return self.stock_quantity >= quantity

    def __str__(self) -> str:
        return f"Product({self.slug}: {self.name})"


@dataclass
class ProductReview:
    id: int
    product_id: int
    user_id: int
    rating: int
    comment: str | None
    is_approved: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not 1 <= self.rating <= 5:
            raise ValueError("Rating must be between 1 and 5")


# ---------------------------------------------------------------------------
# Cart entities
# ---------------------------------------------------------------------------


@dataclass
class CartItem:
    id: int
    cart_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    # Dénormalisé pour la réponse
    product_name: str | None = None
    product_image: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass
class Cart:
    id: int
    user_id: int
    items: list[CartItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0"))

    @property
    def item_count(self) -> int:
        return len(self.items)

    def find_item(self, product_id: int) -> CartItem | None:
        for item in self.items:
            if item.product_id == product_id:
                return item
        return None

    def is_empty(self) -> bool:
        return len(self.items) == 0


# ---------------------------------------------------------------------------
# Wishlist entities
# ---------------------------------------------------------------------------


@dataclass
class WishListItem:
    id: int
    wish_list_id: int
    product_id: int
    product_name: str | None = None
    product_image: str | None = None
    product_price: Decimal | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class WishList:
    id: int
    user_id: int
    items: list[WishListItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Order entities
# ---------------------------------------------------------------------------


@dataclass
class OrderItem:
    id: int
    order_id: int
    product_id: int
    product_name: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Order:
    id: int
    reference: str
    user_id: int
    vendor_id: int | None
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    shipping_amount: Decimal
    total: Decimal
    status: str
    payment_status: str
    payment_gateway: str | None
    shipping_address: str | None
    notes: str | None
    promotion_id: int | None
    items: list[OrderItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    CANCELLABLE_STATUSES = ("pending", "processing")

    def can_cancel(self) -> bool:
        return self.status in self.CANCELLABLE_STATUSES

    def __str__(self) -> str:
        return f"Order({self.reference}: {self.status})"
