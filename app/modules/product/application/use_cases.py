"""Use Cases du module product — application layer."""
import random
import string
from datetime import datetime
from decimal import Decimal

from app.modules.product.domain.entities import (
    Brand,
    Cart,
    Order,
    Product,
    ProductCategory,
    ProductImage,
    ProductReview,
    WishList,
)
from app.modules.product.domain.exceptions import (
    BrandNotFoundError,
    CartEmptyError,
    CartItemNotFoundError,
    CategoryNotFoundError,
    InsufficientStockError,
    OrderCannotBeCancelledError,
    OrderNotFoundError,
    ProductNotFoundError,
    ReviewAlreadyExistsError,
    ReviewNotFoundError,
    SlugAlreadyExistsError,
    WishListItemAlreadyExistsError,
    WishListItemNotFoundError,
)
from app.modules.product.domain.repositories import (
    BrandRepository,
    CartRepository,
    OrderRepository,
    ProductCategoryRepository,
    ProductImageRepository,
    ProductRepository,
    ProductReviewRepository,
    WishListRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams


# ---------------------------------------------------------------------------
# Catalogue — Catégories
# ---------------------------------------------------------------------------


class ListCategoryTreeUseCase:
    def __init__(self, repo: ProductCategoryRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[ProductCategory]:
        return await self._repo.list_tree()


class GetCategoryBySlugUseCase:
    def __init__(self, repo: ProductCategoryRepository) -> None:
        self._repo = repo

    async def execute(self, slug: str) -> ProductCategory:
        cat = await self._repo.get_by_slug(slug)
        if cat is None:
            raise CategoryNotFoundError(slug)
        return cat


class CreateCategoryUseCase:
    def __init__(self, repo: ProductCategoryRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        name: str,
        slug: str,
        parent_id: int | None,
        image: str | None,
        description: str | None,
        is_active: bool,
        sort_order: int,
    ) -> ProductCategory:
        existing = await self._repo.get_by_slug(slug)
        if existing is not None:
            raise SlugAlreadyExistsError(slug)
        return await self._repo.create(
            name=name,
            slug=slug,
            parent_id=parent_id,
            image=image,
            description=description,
            is_active=is_active,
            sort_order=sort_order,
        )


class UpdateCategoryUseCase:
    def __init__(self, repo: ProductCategoryRepository) -> None:
        self._repo = repo

    async def execute(self, category_id: int, **kwargs: object) -> ProductCategory:
        result = await self._repo.update(category_id=category_id, **kwargs)  # type: ignore[arg-type]
        if result is None:
            raise CategoryNotFoundError(category_id)
        return result


class DeleteCategoryUseCase:
    def __init__(self, repo: ProductCategoryRepository) -> None:
        self._repo = repo

    async def execute(self, category_id: int) -> None:
        deleted = await self._repo.soft_delete(category_id)
        if not deleted:
            raise CategoryNotFoundError(category_id)


# ---------------------------------------------------------------------------
# Catalogue — Marques
# ---------------------------------------------------------------------------


class ListBrandsUseCase:
    def __init__(self, repo: BrandRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[Brand]:
        return await self._repo.list_active()


class CreateBrandUseCase:
    def __init__(self, repo: BrandRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        name: str,
        slug: str,
        logo: str | None,
        description: str | None,
        is_active: bool,
    ) -> Brand:
        return await self._repo.create(
            name=name, slug=slug, logo=logo, description=description, is_active=is_active
        )


class UpdateBrandUseCase:
    def __init__(self, repo: BrandRepository) -> None:
        self._repo = repo

    async def execute(self, brand_id: int, **kwargs: object) -> Brand:
        result = await self._repo.update(brand_id=brand_id, **kwargs)  # type: ignore[arg-type]
        if result is None:
            raise BrandNotFoundError(brand_id)
        return result


class DeleteBrandUseCase:
    def __init__(self, repo: BrandRepository) -> None:
        self._repo = repo

    async def execute(self, brand_id: int) -> None:
        deleted = await self._repo.soft_delete(brand_id)
        if not deleted:
            raise BrandNotFoundError(brand_id)


# ---------------------------------------------------------------------------
# Catalogue — Produits
# ---------------------------------------------------------------------------


class ListProductsUseCase:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        category_id: int | None = None,
        brand_id: int | None = None,
        search: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        is_featured: bool | None = None,
    ) -> Page[Product]:
        products, total = await self._repo.list_paginated(
            params=params,
            category_id=category_id,
            brand_id=brand_id,
            search=search,
            min_price=min_price,
            max_price=max_price,
            is_featured=is_featured,
        )
        return Page.create(data=products, total=total, params=params)


class GetProductBySlugUseCase:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(self, slug: str) -> Product:
        product = await self._repo.get_by_slug(slug)
        if product is None:
            raise ProductNotFoundError(slug)
        return product


class CreateProductUseCase:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(
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
        existing = await self._repo.get_by_slug(slug)
        if existing is not None:
            raise SlugAlreadyExistsError(slug)
        return await self._repo.create(
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


class UpdateProductUseCase:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(self, product_id: int, **kwargs: object) -> Product:
        result = await self._repo.update(product_id=product_id, **kwargs)
        if result is None:
            raise ProductNotFoundError(product_id)
        return result


class DeleteProductUseCase:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(self, product_id: int) -> None:
        deleted = await self._repo.soft_delete(product_id)
        if not deleted:
            raise ProductNotFoundError(product_id)


class ToggleProductUseCase:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(self, product_id: int) -> Product:
        result = await self._repo.toggle_active(product_id)
        if result is None:
            raise ProductNotFoundError(product_id)
        return result


class UploadProductImageUseCase:
    def __init__(self, repo: ProductImageRepository) -> None:
        self._repo = repo

    async def execute(
        self, product_id: int, image_path: str, is_primary: bool, sort_order: int
    ) -> ProductImage:
        return await self._repo.add_image(
            product_id=product_id,
            image=image_path,
            is_primary=is_primary,
            sort_order=sort_order,
        )


class DeleteProductImageUseCase:
    def __init__(self, repo: ProductImageRepository) -> None:
        self._repo = repo

    async def execute(self, image_id: int) -> None:
        deleted = await self._repo.delete_image(image_id)
        if not deleted:
            raise ProductNotFoundError(image_id)


# ---------------------------------------------------------------------------
# Avis produits
# ---------------------------------------------------------------------------


class ListProductReviewsUseCase:
    def __init__(self, repo: ProductReviewRepository) -> None:
        self._repo = repo

    async def execute(self, product_id: int, params: PaginationParams) -> Page[ProductReview]:
        reviews, total = await self._repo.list_approved(product_id, params)
        return Page.create(data=reviews, total=total, params=params)


class CreateReviewUseCase:
    def __init__(self, repo: ProductReviewRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        product_id: int,
        user_id: int,
        rating: int,
        comment: str | None,
    ) -> ProductReview:
        already_exists = await self._repo.exists_for_user_product(user_id, product_id)
        if already_exists:
            raise ReviewAlreadyExistsError(user_id, product_id)
        return await self._repo.create(
            product_id=product_id, user_id=user_id, rating=rating, comment=comment
        )


class ListPendingReviewsUseCase:
    def __init__(self, repo: ProductReviewRepository) -> None:
        self._repo = repo

    async def execute(self, params: PaginationParams) -> Page[ProductReview]:
        reviews, total = await self._repo.list_pending(params)
        return Page.create(data=reviews, total=total, params=params)


class ApproveReviewUseCase:
    def __init__(self, repo: ProductReviewRepository) -> None:
        self._repo = repo

    async def execute(self, review_id: int) -> ProductReview:
        result = await self._repo.approve(review_id)
        if result is None:
            raise ReviewNotFoundError(review_id)
        return result


class DeleteReviewUseCase:
    def __init__(self, repo: ProductReviewRepository) -> None:
        self._repo = repo

    async def execute(self, review_id: int) -> None:
        deleted = await self._repo.soft_delete(review_id)
        if not deleted:
            raise ReviewNotFoundError(review_id)


# ---------------------------------------------------------------------------
# Panier
# ---------------------------------------------------------------------------


class GetCartUseCase:
    def __init__(self, cart_repo: CartRepository) -> None:
        self._cart_repo = cart_repo

    async def execute(self, user_id: int) -> Cart:
        return await self._cart_repo.get_or_create(user_id)


class AddToCartUseCase:
    def __init__(self, cart_repo: CartRepository, product_repo: ProductRepository) -> None:
        self._cart_repo = cart_repo
        self._product_repo = product_repo

    async def execute(self, user_id: int, product_id: int, quantity: int) -> Cart:
        product = await self._product_repo.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)

        # Vérifie le stock
        if not product.has_enough_stock(quantity):
            raise InsufficientStockError(product_id, quantity, product.stock_quantity)

        cart = await self._cart_repo.get_or_create(user_id)

        # Vérifie si cumulé la quantité existante ne dépasse pas le stock
        existing_item = cart.find_item(product_id)
        if existing_item is not None:
            total_qty = existing_item.quantity + quantity
            if not product.has_enough_stock(total_qty):
                raise InsufficientStockError(product_id, total_qty, product.stock_quantity)

        # unit_price snapshotté au moment de l'ajout
        await self._cart_repo.add_or_update_item(
            cart_id=cart.id,
            product_id=product_id,
            quantity=quantity,
            unit_price=product.effective_price,
        )
        return await self._cart_repo.get_or_create(user_id)


class UpdateCartItemUseCase:
    def __init__(self, cart_repo: CartRepository, product_repo: ProductRepository) -> None:
        self._cart_repo = cart_repo
        self._product_repo = product_repo

    async def execute(self, user_id: int, product_id: int, quantity: int) -> Cart:
        cart = await self._cart_repo.get_or_create(user_id)
        item = cart.find_item(product_id)
        if item is None:
            raise CartItemNotFoundError(product_id)

        product = await self._product_repo.get_by_id(product_id)
        if product and not product.has_enough_stock(quantity):
            raise InsufficientStockError(product_id, quantity, product.stock_quantity)

        await self._cart_repo.update_item_quantity(
            cart_id=cart.id, product_id=product_id, quantity=quantity
        )
        return await self._cart_repo.get_or_create(user_id)


class RemoveFromCartUseCase:
    def __init__(self, cart_repo: CartRepository) -> None:
        self._cart_repo = cart_repo

    async def execute(self, user_id: int, product_id: int) -> Cart:
        cart = await self._cart_repo.get_or_create(user_id)
        item = cart.find_item(product_id)
        if item is None:
            raise CartItemNotFoundError(product_id)
        await self._cart_repo.remove_item(cart_id=cart.id, product_id=product_id)
        return await self._cart_repo.get_or_create(user_id)


class ClearCartUseCase:
    def __init__(self, cart_repo: CartRepository) -> None:
        self._cart_repo = cart_repo

    async def execute(self, user_id: int) -> Cart:
        cart = await self._cart_repo.get_or_create(user_id)
        await self._cart_repo.clear(cart.id)
        return await self._cart_repo.get_or_create(user_id)


# ---------------------------------------------------------------------------
# Liste de souhaits
# ---------------------------------------------------------------------------


class GetWishListUseCase:
    def __init__(self, repo: WishListRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: int) -> WishList:
        return await self._repo.get_or_create(user_id)


class AddToWishListUseCase:
    def __init__(self, repo: WishListRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: int, product_id: int) -> WishList:
        wl = await self._repo.get_or_create(user_id)
        added = await self._repo.add_item(wl.id, product_id)
        if not added:
            raise WishListItemAlreadyExistsError(product_id)
        return await self._repo.get_or_create(user_id)


class RemoveFromWishListUseCase:
    def __init__(self, repo: WishListRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: int, product_id: int) -> WishList:
        wl = await self._repo.get_or_create(user_id)
        removed = await self._repo.remove_item(wl.id, product_id)
        if not removed:
            raise WishListItemNotFoundError(product_id)
        return await self._repo.get_or_create(user_id)


# ---------------------------------------------------------------------------
# Commandes
# ---------------------------------------------------------------------------


def _generate_order_reference() -> str:
    """Génère une référence unique : ORD-{YYYYMMDD}-{random 6 chiffres}."""
    date_part = datetime.utcnow().strftime("%Y%m%d")
    random_part = "".join(random.choices(string.digits, k=6))
    return f"ORD-{date_part}-{random_part}"


class CreateOrderUseCase:
    """
    Règles métier :
    1. Récupère le panier (erreur si vide)
    2. Valide le stock de chaque article
    3. Calcule le subtotal
    4. Applique promotion (simplifiée — lookup via promotion_id si promotion_code fourni)
    5. Calcule la taxe (simplifiée à 0 pour ce projet — à brancher sur la table taxes)
    6. Génère la référence ORD-{YYYYMMDD}-{6 chiffres}
    7. Crée Order + OrderItems dans une transaction
    8. Vide le panier
    """

    def __init__(
        self,
        cart_repo: CartRepository,
        order_repo: OrderRepository,
        product_repo: ProductRepository,
    ) -> None:
        self._cart_repo = cart_repo
        self._order_repo = order_repo
        self._product_repo = product_repo

    async def execute(
        self,
        user_id: int,
        payment_gateway: str | None,
        shipping_address: str | None,
        promotion_code: str | None,
        notes: str | None,
    ) -> Order:
        # 1. Récupérer le panier
        cart = await self._cart_repo.get_by_user_id(user_id)
        if cart is None or cart.is_empty():
            raise CartEmptyError()

        # 2. Valider le stock + construire les items
        order_items: list[dict] = []
        subtotal = Decimal("0")

        for cart_item in cart.items:
            product = await self._product_repo.get_by_id(cart_item.product_id)
            if product is None:
                raise ProductNotFoundError(cart_item.product_id)
            if not product.has_enough_stock(cart_item.quantity):
                raise InsufficientStockError(
                    cart_item.product_id, cart_item.quantity, product.stock_quantity
                )
            item_subtotal = cart_item.unit_price * cart_item.quantity
            subtotal += item_subtotal
            order_items.append(
                {
                    "product_id": cart_item.product_id,
                    "product_name": product.name,
                    "unit_price": cart_item.unit_price,
                    "quantity": cart_item.quantity,
                    "subtotal": item_subtotal,
                }
            )

        # 3. Calcul taxes (simplifiée à 0)
        tax_amount = Decimal("0")

        # 4. Remise (simplifiée — pas de table promotions branchée ici)
        discount_amount = Decimal("0")

        # 5. Shipping (simplifiée à 0)
        shipping_amount = Decimal("0")

        total = subtotal + tax_amount + shipping_amount - discount_amount

        # 6. Référence unique
        reference = _generate_order_reference()

        # 7. Créer la commande
        order = await self._order_repo.create(
            reference=reference,
            user_id=user_id,
            vendor_id=None,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            shipping_amount=shipping_amount,
            total=total,
            payment_gateway=payment_gateway,
            shipping_address=shipping_address,
            notes=notes,
            promotion_id=None,
            items=order_items,
        )

        # 8. Vider le panier
        await self._cart_repo.clear(cart.id)

        return order


class ListMyOrdersUseCase:
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        user_id: int,
        params: PaginationParams,
        status: str | None = None,
    ) -> Page[Order]:
        orders, total = await self._repo.list_for_user(user_id, params, status)
        return Page.create(data=orders, total=total, params=params)


class GetOrderUseCase:
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def execute(self, order_id: int, user_id: int | None = None) -> Order:
        order = await self._repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        # Si user_id fourni, vérifier que la commande appartient bien à l'utilisateur
        if user_id is not None and order.user_id != user_id:
            raise OrderNotFoundError(order_id)
        return order


class CancelOrderUseCase:
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def execute(self, order_id: int, user_id: int | None = None) -> Order:
        order = await self._repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        if user_id is not None and order.user_id != user_id:
            raise OrderNotFoundError(order_id)
        if not order.can_cancel():
            raise OrderCannotBeCancelledError(order_id, order.status)
        result = await self._repo.cancel(order_id)
        if result is None:
            raise OrderNotFoundError(order_id)
        return result


class ListAllOrdersUseCase:
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        status: str | None = None,
        user_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> Page[Order]:
        orders, total = await self._repo.list_all(
            params=params,
            status=status,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
        )
        return Page.create(data=orders, total=total, params=params)


class UpdateOrderStatusUseCase:
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def execute(self, order_id: int, new_status: str) -> Order:
        result = await self._repo.update_status(order_id, new_status)
        if result is None:
            raise OrderNotFoundError(order_id)
        return result
