"""Modèles SQLAlchemy du module product — tables compatibles Laravel."""
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import BaseModel
from app.database import Base


# ---------------------------------------------------------------------------
# Référentiels
# ---------------------------------------------------------------------------


class UnitModel(BaseModel):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    abbreviation: Mapped[str] = mapped_column(String(20), nullable=False)

    products: Mapped[list["ProductModel"]] = relationship(
        "ProductModel", back_populates="unit", lazy="select"
    )


class ProductCategoryModel(BaseModel):
    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("product_categories.id"), nullable=True
    )
    image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    children: Mapped[list["ProductCategoryModel"]] = relationship(
        "ProductCategoryModel",
        back_populates="parent",
        lazy="selectin",
        foreign_keys=[parent_id],
    )
    parent: Mapped["ProductCategoryModel | None"] = relationship(
        "ProductCategoryModel",
        back_populates="children",
        remote_side="ProductCategoryModel.id",
        foreign_keys=[parent_id],
    )
    products: Mapped[list["ProductModel"]] = relationship(
        "ProductModel", back_populates="category", lazy="select"
    )


class BrandModel(BaseModel):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    products: Mapped[list["ProductModel"]] = relationship(
        "ProductModel", back_populates="brand", lazy="select"
    )


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


class ProductModel(BaseModel):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("product_categories.id"), nullable=False
    )
    brand_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("brands.id"), nullable=True
    )
    unit_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("units.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    # tax_id : pas de FK déclarée ici pour éviter une dépendance circulaire
    # avec le module taxes (géré comme colonne simple — la FK est dans la migration Alembic)
    tax_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    category: Mapped["ProductCategoryModel"] = relationship(
        "ProductCategoryModel", back_populates="products", lazy="selectin"
    )
    brand: Mapped["BrandModel | None"] = relationship(
        "BrandModel", back_populates="products", lazy="selectin"
    )
    unit: Mapped["UnitModel | None"] = relationship(
        "UnitModel", back_populates="products", lazy="selectin"
    )
    images: Mapped[list["ProductImageModel"]] = relationship(
        "ProductImageModel",
        back_populates="product",
        lazy="selectin",
        order_by="ProductImageModel.sort_order",
    )
    reviews: Mapped[list["ProductReviewModel"]] = relationship(
        "ProductReviewModel", back_populates="product", lazy="select"
    )


class ProductImageModel(Base):
    """Pas de soft delete sur les images."""

    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    image: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    from datetime import datetime
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    product: Mapped["ProductModel"] = relationship(
        "ProductModel", back_populates="images"
    )


class ProductReviewModel(BaseModel):
    __tablename__ = "product_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    product: Mapped["ProductModel"] = relationship(
        "ProductModel", back_populates="reviews"
    )


# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------


class CartModel(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False
    )

    from datetime import datetime
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    items: Mapped[list["CartItemModel"]] = relationship(
        "CartItemModel",
        back_populates="cart",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class CartItemModel(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    from datetime import datetime
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", name="uq_cart_items_cart_product"),
    )

    cart: Mapped["CartModel"] = relationship("CartModel", back_populates="items")
    product: Mapped["ProductModel"] = relationship("ProductModel", lazy="selectin")


# ---------------------------------------------------------------------------
# WishList
# ---------------------------------------------------------------------------


class WishListModel(Base):
    __tablename__ = "wish_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False
    )

    from datetime import datetime
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    items: Mapped[list["WishListItemModel"]] = relationship(
        "WishListItemModel",
        back_populates="wish_list",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class WishListItemModel(Base):
    __tablename__ = "wish_list_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wish_list_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("wish_lists.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False
    )

    from datetime import datetime
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "wish_list_id", "product_id", name="uq_wishlist_items_list_product"
        ),
    )

    wish_list: Mapped["WishListModel"] = relationship("WishListModel", back_populates="items")
    product: Mapped["ProductModel"] = relationship("ProductModel", lazy="selectin")


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


class OrderModel(BaseModel):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reference: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    vendor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False
    )
    shipping_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False
    )
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "processing",
            "shipped",
            "delivered",
            "cancelled",
            "refunded",
            name="order_status_enum",
            native_enum=False,
        ),
        default="pending",
        nullable=False,
    )
    payment_status: Mapped[str] = mapped_column(
        Enum("pending", "paid", "refunded", name="order_payment_status_enum", native_enum=False),
        default="pending",
        nullable=False,
    )
    payment_gateway: Mapped[str | None] = mapped_column(String(50), nullable=True)
    shipping_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # promotion_id : pas de FK déclarée ici — dépendance externe gérée via migration
    promotion_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    items: Mapped[list["OrderItemModel"]] = relationship(
        "OrderItemModel",
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    from datetime import datetime
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    order: Mapped["OrderModel"] = relationship("OrderModel", back_populates="items")
    product: Mapped["ProductModel"] = relationship("ProductModel", lazy="selectin")
