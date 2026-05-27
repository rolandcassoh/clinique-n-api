"""Schemas Pydantic v2 du module product."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Catégories
# ---------------------------------------------------------------------------


class ProductCategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    parent_id: int | None
    image: str | None
    description: str | None
    is_active: bool
    sort_order: int
    children: list["ProductCategorySchema"] = []
    created_at: datetime
    updated_at: datetime


ProductCategorySchema.model_rebuild()


class ProductCategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$")
    parent_id: int | None = None
    image: str | None = Field(default=None, max_length=500)
    description: str | None = None
    is_active: bool = True
    sort_order: int = 0


class ProductCategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(
        default=None, min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$"
    )
    parent_id: int | None = None
    image: str | None = None
    description: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


# ---------------------------------------------------------------------------
# Marques
# ---------------------------------------------------------------------------


class BrandSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    logo: str | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class BrandCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$")
    logo: str | None = Field(default=None, max_length=500)
    description: str | None = None
    is_active: bool = True


class BrandUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(
        default=None, min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$"
    )
    logo: str | None = None
    description: str | None = None
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# Images produits
# ---------------------------------------------------------------------------


class ProductImageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    image: str
    is_primary: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Produits
# ---------------------------------------------------------------------------


class ProductListSchema(BaseModel):
    """Schema allégé pour la liste."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    short_description: str | None
    price: Decimal
    discount_price: Decimal | None
    stock_quantity: int
    is_active: bool
    is_featured: bool
    category_name: str | None
    brand_name: str | None
    images: list[ProductImageSchema] = []
    created_at: datetime
    updated_at: datetime


class ProductDetailSchema(BaseModel):
    """Schema complet avec images et review_summary."""

    model_config = ConfigDict(from_attributes=True)

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
    category_name: str | None
    brand_name: str | None
    unit_name: str | None
    images: list[ProductImageSchema] = []
    created_at: datetime
    updated_at: datetime


class ProductCreateRequest(BaseModel):
    vendor_id: int
    category_id: int
    brand_id: int | None = None
    unit_id: int | None = None
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    short_description: str | None = Field(default=None, max_length=500)
    price: Decimal = Field(..., gt=0)
    discount_price: Decimal | None = Field(default=None, gt=0)
    stock_quantity: int = Field(default=0, ge=0)
    sku: str | None = Field(default=None, max_length=100)
    is_active: bool = True
    is_featured: bool = False
    weight: Decimal | None = None
    tax_id: int | None = None


class ProductUpdateRequest(BaseModel):
    category_id: int | None = None
    brand_id: int | None = None
    unit_id: int | None = None
    name: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(
        default=None, min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$"
    )
    description: str | None = None
    short_description: str | None = None
    price: Decimal | None = Field(default=None, gt=0)
    discount_price: Decimal | None = None
    stock_quantity: int | None = Field(default=None, ge=0)
    sku: str | None = None
    is_active: bool | None = None
    is_featured: bool | None = None
    weight: Decimal | None = None
    tax_id: int | None = None


# ---------------------------------------------------------------------------
# Avis produits
# ---------------------------------------------------------------------------


class ProductReviewSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    user_id: int
    rating: int
    comment: str | None
    is_approved: bool
    created_at: datetime
    updated_at: datetime


class ProductReviewCreateRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


# ---------------------------------------------------------------------------
# Panier
# ---------------------------------------------------------------------------


class CartItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cart_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    product_name: str | None
    product_image: str | None
    created_at: datetime
    updated_at: datetime


class CartSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    items: list[CartItemSchema] = []
    total: Decimal
    item_count: int
    created_at: datetime
    updated_at: datetime


class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(..., ge=1)


# ---------------------------------------------------------------------------
# Liste de souhaits
# ---------------------------------------------------------------------------


class WishListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wish_list_id: int
    product_id: int
    product_name: str | None
    product_image: str | None
    product_price: Decimal | None
    created_at: datetime
    updated_at: datetime


class WishListSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    items: list[WishListItemSchema] = []
    created_at: datetime
    updated_at: datetime


class AddToWishListRequest(BaseModel):
    product_id: int


# ---------------------------------------------------------------------------
# Commandes
# ---------------------------------------------------------------------------


class OrderItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    product_id: int
    product_name: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal
    created_at: datetime
    updated_at: datetime


class OrderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    items: list[OrderItemSchema] = []
    created_at: datetime
    updated_at: datetime


class CreateOrderRequest(BaseModel):
    payment_gateway: str | None = Field(default=None, max_length=50)
    shipping_address: str | None = None
    promotion_code: str | None = None
    notes: str | None = None


class UpdateOrderStatusRequest(BaseModel):
    status: str = Field(..., pattern=r"^(processing|shipped|delivered)$")
