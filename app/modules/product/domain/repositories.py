"""Interfaces (ABC) des repositories du module product."""
from abc import ABC, abstractmethod
from decimal import Decimal

from app.modules.product.domain.entities import (
    Brand,
    Cart,
    CartItem,
    Order,
    Product,
    ProductCategory,
    ProductImage,
    ProductReview,
    Unit,
    WishList,
)
from app.shared.schemas.pagination import PaginationParams


class ProductCategoryRepository(ABC):
    @abstractmethod
    async def list_tree(self) -> list[ProductCategory]:
        """Retourne les catégories racines avec leurs sous-catégories."""
        ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> ProductCategory | None:
        ...

    @abstractmethod
    async def get_by_id(self, category_id: int) -> ProductCategory | None:
        ...

    @abstractmethod
    async def create(
        self,
        name: str,
        slug: str,
        parent_id: int | None,
        image: str | None,
        description: str | None,
        is_active: bool,
        sort_order: int,
    ) -> ProductCategory:
        ...

    @abstractmethod
    async def update(
        self,
        category_id: int,
        name: str | None,
        slug: str | None,
        parent_id: int | None,
        image: str | None,
        description: str | None,
        is_active: bool | None,
        sort_order: int | None,
    ) -> ProductCategory | None:
        ...

    @abstractmethod
    async def soft_delete(self, category_id: int) -> bool:
        ...


class BrandRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[Brand]:
        ...

    @abstractmethod
    async def get_by_id(self, brand_id: int) -> Brand | None:
        ...

    @abstractmethod
    async def create(
        self,
        name: str,
        slug: str,
        logo: str | None,
        description: str | None,
        is_active: bool,
    ) -> Brand:
        ...

    @abstractmethod
    async def update(
        self,
        brand_id: int,
        name: str | None,
        slug: str | None,
        logo: str | None,
        description: str | None,
        is_active: bool | None,
    ) -> Brand | None:
        ...

    @abstractmethod
    async def soft_delete(self, brand_id: int) -> bool:
        ...


class UnitRepository(ABC):
    @abstractmethod
    async def get_by_id(self, unit_id: int) -> Unit | None:
        ...


class ProductRepository(ABC):
    @abstractmethod
    async def list_paginated(
        self,
        params: PaginationParams,
        category_id: int | None = None,
        brand_id: int | None = None,
        search: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        is_featured: bool | None = None,
    ) -> tuple[list[Product], int]:
        ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Product | None:
        ...

    @abstractmethod
    async def get_by_id(self, product_id: int) -> Product | None:
        ...

    @abstractmethod
    async def create(
        self,
        vendor_id: int,
        category_id: int,
        brand_id: int | None,
        unit_id: int | None,
        name: str,
        slug: str,
        description: str | None,
        short_description: str | None,
        price: Decimal,
        discount_price: Decimal | None,
        stock_quantity: int,
        sku: str | None,
        is_active: bool,
        is_featured: bool,
        weight: Decimal | None,
        tax_id: int | None,
    ) -> Product:
        ...

    @abstractmethod
    async def update(
        self,
        product_id: int,
        **kwargs: object,
    ) -> Product | None:
        ...

    @abstractmethod
    async def soft_delete(self, product_id: int) -> bool:
        ...

    @abstractmethod
    async def toggle_active(self, product_id: int) -> Product | None:
        ...


class ProductImageRepository(ABC):
    @abstractmethod
    async def add_image(
        self,
        product_id: int,
        image: str,
        is_primary: bool,
        sort_order: int,
    ) -> ProductImage:
        ...

    @abstractmethod
    async def delete_image(self, image_id: int) -> bool:
        ...

    @abstractmethod
    async def list_for_product(self, product_id: int) -> list[ProductImage]:
        ...


class ProductReviewRepository(ABC):
    @abstractmethod
    async def list_approved(
        self,
        product_id: int,
        params: PaginationParams,
    ) -> tuple[list[ProductReview], int]:
        ...

    @abstractmethod
    async def list_pending(
        self,
        params: PaginationParams,
    ) -> tuple[list[ProductReview], int]:
        ...

    @abstractmethod
    async def get_by_id(self, review_id: int) -> ProductReview | None:
        ...

    @abstractmethod
    async def exists_for_user_product(self, user_id: int, product_id: int) -> bool:
        ...

    @abstractmethod
    async def create(
        self,
        product_id: int,
        user_id: int,
        rating: int,
        comment: str | None,
    ) -> ProductReview:
        ...

    @abstractmethod
    async def approve(self, review_id: int) -> ProductReview | None:
        ...

    @abstractmethod
    async def soft_delete(self, review_id: int) -> bool:
        ...


class CartRepository(ABC):
    @abstractmethod
    async def get_or_create(self, user_id: int) -> Cart:
        ...

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> Cart | None:
        ...

    @abstractmethod
    async def add_or_update_item(
        self,
        cart_id: int,
        product_id: int,
        quantity: int,
        unit_price: Decimal,
    ) -> CartItem:
        """Si product_id existe déjà, additionne les quantités."""
        ...

    @abstractmethod
    async def update_item_quantity(
        self,
        cart_id: int,
        product_id: int,
        quantity: int,
    ) -> CartItem | None:
        ...

    @abstractmethod
    async def remove_item(self, cart_id: int, product_id: int) -> bool:
        ...

    @abstractmethod
    async def clear(self, cart_id: int) -> None:
        ...


class WishListRepository(ABC):
    @abstractmethod
    async def get_or_create(self, user_id: int) -> WishList:
        ...

    @abstractmethod
    async def add_item(self, wish_list_id: int, product_id: int) -> bool:
        """Retourne False si déjà présent."""
        ...

    @abstractmethod
    async def remove_item(self, wish_list_id: int, product_id: int) -> bool:
        ...


class OrderRepository(ABC):
    @abstractmethod
    async def create(
        self,
        reference: str,
        user_id: int,
        vendor_id: int | None,
        subtotal: Decimal,
        discount_amount: Decimal,
        tax_amount: Decimal,
        shipping_amount: Decimal,
        total: Decimal,
        payment_gateway: str | None,
        shipping_address: str | None,
        notes: str | None,
        promotion_id: int | None,
        items: list[dict],
    ) -> Order:
        ...

    @abstractmethod
    async def list_for_user(
        self,
        user_id: int,
        params: PaginationParams,
        status: str | None = None,
    ) -> tuple[list[Order], int]:
        ...

    @abstractmethod
    async def list_all(
        self,
        params: PaginationParams,
        status: str | None = None,
        user_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[list[Order], int]:
        ...

    @abstractmethod
    async def get_by_id(self, order_id: int) -> Order | None:
        ...

    @abstractmethod
    async def update_status(self, order_id: int, new_status: str) -> Order | None:
        ...

    @abstractmethod
    async def cancel(self, order_id: int) -> Order | None:
        ...
