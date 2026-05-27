"""Implémentations SQLAlchemy async des repositories du module product."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.product.domain.entities import (
    Brand,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Product,
    ProductCategory,
    ProductImage,
    ProductReview,
    Unit,
    WishList,
    WishListItem,
)
from app.modules.product.domain.repositories import (
    BrandRepository,
    CartRepository,
    OrderRepository,
    ProductCategoryRepository,
    ProductImageRepository,
    ProductRepository,
    ProductReviewRepository,
    UnitRepository,
    WishListRepository,
)
from app.modules.product.infrastructure.models import (
    BrandModel,
    CartItemModel,
    CartModel,
    OrderItemModel,
    OrderModel,
    ProductCategoryModel,
    ProductImageModel,
    ProductModel,
    ProductReviewModel,
    UnitModel,
    WishListItemModel,
    WishListModel,
)
from app.shared.schemas.pagination import PaginationParams


# ---------------------------------------------------------------------------
# Mappers  entity ← model
# ---------------------------------------------------------------------------


def _cat_to_entity(m: ProductCategoryModel, children: list[ProductCategory] | None = None) -> ProductCategory:
    return ProductCategory(
        id=m.id,
        name=m.name,
        slug=m.slug,
        parent_id=m.parent_id,
        image=m.image,
        description=m.description,
        is_active=m.is_active,
        sort_order=m.sort_order,
        children=children or [],
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _brand_to_entity(m: BrandModel) -> Brand:
    return Brand(
        id=m.id,
        name=m.name,
        slug=m.slug,
        logo=m.logo,
        description=m.description,
        is_active=m.is_active,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _unit_to_entity(m: UnitModel) -> Unit:
    return Unit(
        id=m.id,
        name=m.name,
        abbreviation=m.abbreviation,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _image_to_entity(m: ProductImageModel) -> ProductImage:
    return ProductImage(
        id=m.id,
        product_id=m.product_id,
        image=m.image,
        is_primary=m.is_primary,
        sort_order=m.sort_order,
        created_at=m.created_at or datetime.now(),
        updated_at=m.updated_at or datetime.now(),
    )


def _product_to_entity(m: ProductModel) -> Product:
    images = [_image_to_entity(img) for img in (m.images or [])]
    return Product(
        id=m.id,
        vendor_id=m.vendor_id,
        category_id=m.category_id,
        brand_id=m.brand_id,
        unit_id=m.unit_id,
        name=m.name,
        slug=m.slug,
        description=m.description,
        short_description=m.short_description,
        price=m.price,
        discount_price=m.discount_price,
        stock_quantity=m.stock_quantity,
        sku=m.sku,
        is_active=m.is_active,
        is_featured=m.is_featured,
        weight=m.weight,
        tax_id=m.tax_id,
        category_name=m.category.name if m.category else None,
        brand_name=m.brand.name if m.brand else None,
        unit_name=m.unit.name if m.unit else None,
        images=images,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _review_to_entity(m: ProductReviewModel) -> ProductReview:
    return ProductReview(
        id=m.id,
        product_id=m.product_id,
        user_id=m.user_id,
        rating=m.rating,
        comment=m.comment,
        is_approved=m.is_approved,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _cart_item_to_entity(m: CartItemModel) -> CartItem:
    product = m.product
    primary_image: str | None = None
    if product and product.images:
        primaries = [img for img in product.images if img.is_primary]
        primary_image = primaries[0].image if primaries else product.images[0].image
    return CartItem(
        id=m.id,
        cart_id=m.cart_id,
        product_id=m.product_id,
        quantity=m.quantity,
        unit_price=m.unit_price,
        product_name=product.name if product else None,
        product_image=primary_image,
        created_at=m.created_at or datetime.now(),
        updated_at=m.updated_at or datetime.now(),
    )


def _cart_to_entity(m: CartModel) -> Cart:
    return Cart(
        id=m.id,
        user_id=m.user_id,
        items=[_cart_item_to_entity(i) for i in (m.items or [])],
        created_at=m.created_at or datetime.now(),
        updated_at=m.updated_at or datetime.now(),
    )


def _wishlist_item_to_entity(m: WishListItemModel) -> WishListItem:
    product = m.product
    primary_image: str | None = None
    if product and product.images:
        primaries = [img for img in product.images if img.is_primary]
        primary_image = primaries[0].image if primaries else product.images[0].image
    return WishListItem(
        id=m.id,
        wish_list_id=m.wish_list_id,
        product_id=m.product_id,
        product_name=product.name if product else None,
        product_image=primary_image,
        product_price=product.price if product else None,
        created_at=m.created_at or datetime.now(),
        updated_at=m.updated_at or datetime.now(),
    )


def _wishlist_to_entity(m: WishListModel) -> WishList:
    return WishList(
        id=m.id,
        user_id=m.user_id,
        items=[_wishlist_item_to_entity(i) for i in (m.items or [])],
        created_at=m.created_at or datetime.now(),
        updated_at=m.updated_at or datetime.now(),
    )


def _order_item_to_entity(m: OrderItemModel) -> OrderItem:
    return OrderItem(
        id=m.id,
        order_id=m.order_id,
        product_id=m.product_id,
        product_name=m.product_name,
        unit_price=m.unit_price,
        quantity=m.quantity,
        subtotal=m.subtotal,
        created_at=m.created_at or datetime.now(),
        updated_at=m.updated_at or datetime.now(),
    )


def _order_to_entity(m: OrderModel) -> Order:
    return Order(
        id=m.id,
        reference=m.reference,
        user_id=m.user_id,
        vendor_id=m.vendor_id,
        subtotal=m.subtotal,
        discount_amount=m.discount_amount,
        tax_amount=m.tax_amount,
        shipping_amount=m.shipping_amount,
        total=m.total,
        status=m.status,
        payment_status=m.payment_status,
        payment_gateway=m.payment_gateway,
        shipping_address=m.shipping_address,
        notes=m.notes,
        promotion_id=m.promotion_id,
        items=[_order_item_to_entity(i) for i in (m.items or [])],
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------


class SQLAlchemyProductCategoryRepository(ProductCategoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_tree(self) -> list[ProductCategory]:
        # Charge toutes les catégories actives non supprimées
        q = (
            select(ProductCategoryModel)
            .where(
                ProductCategoryModel.deleted_at.is_(None),
                ProductCategoryModel.is_active.is_(True),
            )
            .order_by(ProductCategoryModel.sort_order)
        )
        rows = (await self._session.execute(q)).scalars().all()

        # Construit l'arbre en mémoire
        by_id: dict[int, ProductCategory] = {}
        for row in rows:
            by_id[row.id] = _cat_to_entity(row)

        roots: list[ProductCategory] = []
        for row in rows:
            entity = by_id[row.id]
            if row.parent_id is None:
                roots.append(entity)
            elif row.parent_id in by_id:
                by_id[row.parent_id].children.append(entity)

        return roots

    async def get_by_slug(self, slug: str) -> ProductCategory | None:
        q = select(ProductCategoryModel).where(
            ProductCategoryModel.slug == slug,
            ProductCategoryModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _cat_to_entity(row) if row else None

    async def get_by_id(self, category_id: int) -> ProductCategory | None:
        q = select(ProductCategoryModel).where(
            ProductCategoryModel.id == category_id,
            ProductCategoryModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _cat_to_entity(row) if row else None

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
        cat = ProductCategoryModel(
            name=name,
            slug=slug,
            parent_id=parent_id,
            image=image,
            description=description,
            is_active=is_active,
            sort_order=sort_order,
        )
        self._session.add(cat)
        await self._session.flush()
        await self._session.refresh(cat)
        return _cat_to_entity(cat)

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
        q = select(ProductCategoryModel).where(
            ProductCategoryModel.id == category_id,
            ProductCategoryModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        if name is not None:
            row.name = name
        if slug is not None:
            row.slug = slug
        if parent_id is not None:
            row.parent_id = parent_id
        if image is not None:
            row.image = image
        if description is not None:
            row.description = description
        if is_active is not None:
            row.is_active = is_active
        if sort_order is not None:
            row.sort_order = sort_order
        await self._session.flush()
        await self._session.refresh(row)
        return _cat_to_entity(row)

    async def soft_delete(self, category_id: int) -> bool:
        q = select(ProductCategoryModel).where(
            ProductCategoryModel.id == category_id,
            ProductCategoryModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        row.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True


class SQLAlchemyBrandRepository(BrandRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[Brand]:
        q = (
            select(BrandModel)
            .where(BrandModel.deleted_at.is_(None), BrandModel.is_active.is_(True))
            .order_by(BrandModel.name)
        )
        rows = (await self._session.execute(q)).scalars().all()
        return [_brand_to_entity(r) for r in rows]

    async def get_by_id(self, brand_id: int) -> Brand | None:
        q = select(BrandModel).where(
            BrandModel.id == brand_id, BrandModel.deleted_at.is_(None)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _brand_to_entity(row) if row else None

    async def create(
        self,
        name: str,
        slug: str,
        logo: str | None,
        description: str | None,
        is_active: bool,
    ) -> Brand:
        brand = BrandModel(
            name=name, slug=slug, logo=logo, description=description, is_active=is_active
        )
        self._session.add(brand)
        await self._session.flush()
        await self._session.refresh(brand)
        return _brand_to_entity(brand)

    async def update(
        self,
        brand_id: int,
        name: str | None,
        slug: str | None,
        logo: str | None,
        description: str | None,
        is_active: bool | None,
    ) -> Brand | None:
        q = select(BrandModel).where(
            BrandModel.id == brand_id, BrandModel.deleted_at.is_(None)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        if name is not None:
            row.name = name
        if slug is not None:
            row.slug = slug
        if logo is not None:
            row.logo = logo
        if description is not None:
            row.description = description
        if is_active is not None:
            row.is_active = is_active
        await self._session.flush()
        await self._session.refresh(row)
        return _brand_to_entity(row)

    async def soft_delete(self, brand_id: int) -> bool:
        q = select(BrandModel).where(
            BrandModel.id == brand_id, BrandModel.deleted_at.is_(None)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        row.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True


class SQLAlchemyUnitRepository(UnitRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, unit_id: int) -> Unit | None:
        q = select(UnitModel).where(
            UnitModel.id == unit_id, UnitModel.deleted_at.is_(None)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _unit_to_entity(row) if row else None


class SQLAlchemyProductRepository(ProductRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        base_q = select(ProductModel).where(
            ProductModel.deleted_at.is_(None),
            ProductModel.is_active.is_(True),
        )
        if category_id is not None:
            base_q = base_q.where(ProductModel.category_id == category_id)
        if brand_id is not None:
            base_q = base_q.where(ProductModel.brand_id == brand_id)
        if search:
            base_q = base_q.where(
                ProductModel.name.ilike(f"%{search}%")
                | ProductModel.short_description.ilike(f"%{search}%")
            )
        if min_price is not None:
            base_q = base_q.where(ProductModel.price >= min_price)
        if max_price is not None:
            base_q = base_q.where(ProductModel.price <= max_price)
        if is_featured is not None:
            base_q = base_q.where(ProductModel.is_featured == is_featured)

        count_q = select(func.count()).select_from(base_q.subquery())
        total: int = (await self._session.execute(count_q)).scalar_one()

        rows_q = (
            base_q.order_by(ProductModel.created_at.desc())
            .offset(params.offset)
            .limit(params.per_page)
        )
        rows = (await self._session.execute(rows_q)).scalars().all()
        return [_product_to_entity(r) for r in rows], total

    async def get_by_slug(self, slug: str) -> Product | None:
        q = select(ProductModel).where(
            ProductModel.slug == slug, ProductModel.deleted_at.is_(None)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _product_to_entity(row) if row else None

    async def get_by_id(self, product_id: int) -> Product | None:
        q = select(ProductModel).where(
            ProductModel.id == product_id, ProductModel.deleted_at.is_(None)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _product_to_entity(row) if row else None

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
        product = ProductModel(
            vendor_id=vendor_id,
            category_id=category_id,
            brand_id=brand_id,
            unit_id=unit_id,
            name=name,
            slug=slug,
            description=description,
            short_description=short_description,
            price=price,
            discount_price=discount_price,
            stock_quantity=stock_quantity,
            sku=sku,
            is_active=is_active,
            is_featured=is_featured,
            weight=weight,
            tax_id=tax_id,
        )
        self._session.add(product)
        await self._session.flush()
        await self._session.refresh(product)
        return _product_to_entity(product)

    async def update(self, product_id: int, **kwargs: object) -> Product | None:
        q = select(ProductModel).where(
            ProductModel.id == product_id, ProductModel.deleted_at.is_(None)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        for field_name, value in kwargs.items():
            if value is not None and hasattr(row, field_name):
                setattr(row, field_name, value)
        await self._session.flush()
        await self._session.refresh(row)
        return _product_to_entity(row)

    async def soft_delete(self, product_id: int) -> bool:
        q = select(ProductModel).where(
            ProductModel.id == product_id, ProductModel.deleted_at.is_(None)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        row.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True

    async def toggle_active(self, product_id: int) -> Product | None:
        q = select(ProductModel).where(
            ProductModel.id == product_id, ProductModel.deleted_at.is_(None)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        row.is_active = not row.is_active
        await self._session.flush()
        await self._session.refresh(row)
        return _product_to_entity(row)


class SQLAlchemyProductImageRepository(ProductImageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_image(
        self,
        product_id: int,
        image: str,
        is_primary: bool,
        sort_order: int,
    ) -> ProductImage:
        img = ProductImageModel(
            product_id=product_id,
            image=image,
            is_primary=is_primary,
            sort_order=sort_order,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self._session.add(img)
        await self._session.flush()
        await self._session.refresh(img)
        return _image_to_entity(img)

    async def delete_image(self, image_id: int) -> bool:
        q = select(ProductImageModel).where(ProductImageModel.id == image_id)
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True

    async def list_for_product(self, product_id: int) -> list[ProductImage]:
        q = (
            select(ProductImageModel)
            .where(ProductImageModel.product_id == product_id)
            .order_by(ProductImageModel.sort_order)
        )
        rows = (await self._session.execute(q)).scalars().all()
        return [_image_to_entity(r) for r in rows]


class SQLAlchemyProductReviewRepository(ProductReviewRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_approved(
        self, product_id: int, params: PaginationParams
    ) -> tuple[list[ProductReview], int]:
        base_q = select(ProductReviewModel).where(
            ProductReviewModel.product_id == product_id,
            ProductReviewModel.is_approved.is_(True),
            ProductReviewModel.deleted_at.is_(None),
        )
        total: int = (
            await self._session.execute(
                select(func.count()).select_from(base_q.subquery())
            )
        ).scalar_one()
        rows = (
            await self._session.execute(
                base_q.order_by(ProductReviewModel.created_at.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_review_to_entity(r) for r in rows], total

    async def list_pending(
        self, params: PaginationParams
    ) -> tuple[list[ProductReview], int]:
        base_q = select(ProductReviewModel).where(
            ProductReviewModel.is_approved.is_(False),
            ProductReviewModel.deleted_at.is_(None),
        )
        total: int = (
            await self._session.execute(
                select(func.count()).select_from(base_q.subquery())
            )
        ).scalar_one()
        rows = (
            await self._session.execute(
                base_q.order_by(ProductReviewModel.created_at.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_review_to_entity(r) for r in rows], total

    async def get_by_id(self, review_id: int) -> ProductReview | None:
        q = select(ProductReviewModel).where(
            ProductReviewModel.id == review_id,
            ProductReviewModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _review_to_entity(row) if row else None

    async def exists_for_user_product(self, user_id: int, product_id: int) -> bool:
        q = select(func.count()).where(
            ProductReviewModel.user_id == user_id,
            ProductReviewModel.product_id == product_id,
            ProductReviewModel.deleted_at.is_(None),
        )
        count: int = (await self._session.execute(q)).scalar_one()
        return count > 0

    async def create(
        self,
        product_id: int,
        user_id: int,
        rating: int,
        comment: str | None,
    ) -> ProductReview:
        review = ProductReviewModel(
            product_id=product_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            is_approved=False,
        )
        self._session.add(review)
        await self._session.flush()
        await self._session.refresh(review)
        return _review_to_entity(review)

    async def approve(self, review_id: int) -> ProductReview | None:
        q = select(ProductReviewModel).where(
            ProductReviewModel.id == review_id,
            ProductReviewModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        row.is_approved = True
        await self._session.flush()
        await self._session.refresh(row)
        return _review_to_entity(row)

    async def soft_delete(self, review_id: int) -> bool:
        q = select(ProductReviewModel).where(
            ProductReviewModel.id == review_id,
            ProductReviewModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        row.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True


class SQLAlchemyCartRepository(CartRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _load_cart(self, cart_id: int) -> CartModel | None:
        q = select(CartModel).where(CartModel.id == cart_id)
        return (await self._session.execute(q)).scalar_one_or_none()

    async def get_or_create(self, user_id: int) -> Cart:
        q = select(CartModel).where(CartModel.user_id == user_id)
        cart = (await self._session.execute(q)).scalar_one_or_none()
        if cart is None:
            now = datetime.utcnow()
            cart = CartModel(user_id=user_id, created_at=now, updated_at=now)
            self._session.add(cart)
            await self._session.flush()
            await self._session.refresh(cart)
        return _cart_to_entity(cart)

    async def get_by_user_id(self, user_id: int) -> Cart | None:
        q = select(CartModel).where(CartModel.user_id == user_id)
        cart = (await self._session.execute(q)).scalar_one_or_none()
        return _cart_to_entity(cart) if cart else None

    async def add_or_update_item(
        self,
        cart_id: int,
        product_id: int,
        quantity: int,
        unit_price: Decimal,
    ) -> CartItem:
        # Cherche si l'item existe déjà
        q = select(CartItemModel).where(
            CartItemModel.cart_id == cart_id,
            CartItemModel.product_id == product_id,
        )
        existing = (await self._session.execute(q)).scalar_one_or_none()
        now = datetime.utcnow()
        if existing is not None:
            # Additionne les quantités (règle métier)
            existing.quantity += quantity
            existing.updated_at = now
            await self._session.flush()
            await self._session.refresh(existing)
            return _cart_item_to_entity(existing)
        else:
            item = CartItemModel(
                cart_id=cart_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                created_at=now,
                updated_at=now,
            )
            self._session.add(item)
            await self._session.flush()
            await self._session.refresh(item)
            return _cart_item_to_entity(item)

    async def update_item_quantity(
        self,
        cart_id: int,
        product_id: int,
        quantity: int,
    ) -> CartItem | None:
        q = select(CartItemModel).where(
            CartItemModel.cart_id == cart_id,
            CartItemModel.product_id == product_id,
        )
        item = (await self._session.execute(q)).scalar_one_or_none()
        if item is None:
            return None
        item.quantity = quantity
        item.updated_at = datetime.utcnow()
        await self._session.flush()
        await self._session.refresh(item)
        return _cart_item_to_entity(item)

    async def remove_item(self, cart_id: int, product_id: int) -> bool:
        q = select(CartItemModel).where(
            CartItemModel.cart_id == cart_id,
            CartItemModel.product_id == product_id,
        )
        item = (await self._session.execute(q)).scalar_one_or_none()
        if item is None:
            return False
        await self._session.delete(item)
        await self._session.flush()
        return True

    async def clear(self, cart_id: int) -> None:
        q = select(CartItemModel).where(CartItemModel.cart_id == cart_id)
        items = (await self._session.execute(q)).scalars().all()
        for item in items:
            await self._session.delete(item)
        await self._session.flush()


class SQLAlchemyWishListRepository(WishListRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self, user_id: int) -> WishList:
        q = select(WishListModel).where(WishListModel.user_id == user_id)
        wl = (await self._session.execute(q)).scalar_one_or_none()
        if wl is None:
            now = datetime.utcnow()
            wl = WishListModel(user_id=user_id, created_at=now, updated_at=now)
            self._session.add(wl)
            await self._session.flush()
            await self._session.refresh(wl)
        return _wishlist_to_entity(wl)

    async def add_item(self, wish_list_id: int, product_id: int) -> bool:
        q = select(WishListItemModel).where(
            WishListItemModel.wish_list_id == wish_list_id,
            WishListItemModel.product_id == product_id,
        )
        existing = (await self._session.execute(q)).scalar_one_or_none()
        if existing is not None:
            return False
        now = datetime.utcnow()
        item = WishListItemModel(
            wish_list_id=wish_list_id,
            product_id=product_id,
            created_at=now,
            updated_at=now,
        )
        self._session.add(item)
        await self._session.flush()
        return True

    async def remove_item(self, wish_list_id: int, product_id: int) -> bool:
        q = select(WishListItemModel).where(
            WishListItemModel.wish_list_id == wish_list_id,
            WishListItemModel.product_id == product_id,
        )
        item = (await self._session.execute(q)).scalar_one_or_none()
        if item is None:
            return False
        await self._session.delete(item)
        await self._session.flush()
        return True


class SQLAlchemyOrderRepository(OrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        now = datetime.utcnow()
        order = OrderModel(
            reference=reference,
            user_id=user_id,
            vendor_id=vendor_id,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            shipping_amount=shipping_amount,
            total=total,
            payment_gateway=payment_gateway,
            shipping_address=shipping_address,
            notes=notes,
            promotion_id=promotion_id,
            status="pending",
            payment_status="pending",
        )
        self._session.add(order)
        await self._session.flush()

        for item_data in items:
            oi = OrderItemModel(
                order_id=order.id,
                product_id=item_data["product_id"],
                product_name=item_data["product_name"],
                unit_price=item_data["unit_price"],
                quantity=item_data["quantity"],
                subtotal=item_data["subtotal"],
                created_at=now,
                updated_at=now,
            )
            self._session.add(oi)

        await self._session.flush()
        await self._session.refresh(order)
        return _order_to_entity(order)

    async def list_for_user(
        self,
        user_id: int,
        params: PaginationParams,
        status: str | None = None,
    ) -> tuple[list[Order], int]:
        base_q = select(OrderModel).where(
            OrderModel.user_id == user_id,
            OrderModel.deleted_at.is_(None),
        )
        if status:
            base_q = base_q.where(OrderModel.status == status)
        total: int = (
            await self._session.execute(
                select(func.count()).select_from(base_q.subquery())
            )
        ).scalar_one()
        rows = (
            await self._session.execute(
                base_q.order_by(OrderModel.created_at.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_order_to_entity(r) for r in rows], total

    async def list_all(
        self,
        params: PaginationParams,
        status: str | None = None,
        user_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[list[Order], int]:
        base_q = select(OrderModel).where(OrderModel.deleted_at.is_(None))
        if status:
            base_q = base_q.where(OrderModel.status == status)
        if user_id:
            base_q = base_q.where(OrderModel.user_id == user_id)
        if date_from:
            base_q = base_q.where(OrderModel.created_at >= date_from)
        if date_to:
            base_q = base_q.where(OrderModel.created_at <= date_to)
        total: int = (
            await self._session.execute(
                select(func.count()).select_from(base_q.subquery())
            )
        ).scalar_one()
        rows = (
            await self._session.execute(
                base_q.order_by(OrderModel.created_at.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_order_to_entity(r) for r in rows], total

    async def get_by_id(self, order_id: int) -> Order | None:
        q = select(OrderModel).where(
            OrderModel.id == order_id,
            OrderModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _order_to_entity(row) if row else None

    async def update_status(self, order_id: int, new_status: str) -> Order | None:
        q = select(OrderModel).where(
            OrderModel.id == order_id, OrderModel.deleted_at.is_(None)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        row.status = new_status
        await self._session.flush()
        await self._session.refresh(row)
        return _order_to_entity(row)

    async def cancel(self, order_id: int) -> Order | None:
        return await self.update_status(order_id, "cancelled")
