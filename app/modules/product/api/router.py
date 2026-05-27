"""Router FastAPI du module product (~42 endpoints)."""
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.core.storage.port import StoragePort
from app.core.storage.local_adapter import LocalStorageAdapter
from app.database import get_db
from app.modules.product.api.schemas import (
    AddToCartRequest,
    AddToWishListRequest,
    BrandCreateRequest,
    BrandSchema,
    BrandUpdateRequest,
    CartSchema,
    CreateOrderRequest,
    OrderSchema,
    ProductCategoryCreateRequest,
    ProductCategorySchema,
    ProductCategoryUpdateRequest,
    ProductCreateRequest,
    ProductDetailSchema,
    ProductImageSchema,
    ProductListSchema,
    ProductReviewCreateRequest,
    ProductReviewSchema,
    ProductUpdateRequest,
    UpdateCartItemRequest,
    UpdateOrderStatusRequest,
    WishListSchema,
)
from app.modules.product.application.use_cases import (
    AddToCartUseCase,
    AddToWishListUseCase,
    ApproveReviewUseCase,
    CancelOrderUseCase,
    ClearCartUseCase,
    CreateBrandUseCase,
    CreateCategoryUseCase,
    CreateOrderUseCase,
    CreateProductUseCase,
    CreateReviewUseCase,
    DeleteBrandUseCase,
    DeleteCategoryUseCase,
    DeleteProductImageUseCase,
    DeleteProductUseCase,
    DeleteReviewUseCase,
    GetCartUseCase,
    GetCategoryBySlugUseCase,
    GetOrderUseCase,
    GetProductBySlugUseCase,
    GetWishListUseCase,
    ListAllOrdersUseCase,
    ListBrandsUseCase,
    ListCategoryTreeUseCase,
    ListMyOrdersUseCase,
    ListPendingReviewsUseCase,
    ListProductReviewsUseCase,
    ListProductsUseCase,
    RemoveFromCartUseCase,
    RemoveFromWishListUseCase,
    ToggleProductUseCase,
    UpdateBrandUseCase,
    UpdateCategoryUseCase,
    UpdateCartItemUseCase,
    UpdateOrderStatusUseCase,
    UpdateProductUseCase,
    UploadProductImageUseCase,
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
from app.modules.product.infrastructure.repositories import (
    SQLAlchemyBrandRepository,
    SQLAlchemyCartRepository,
    SQLAlchemyOrderRepository,
    SQLAlchemyProductCategoryRepository,
    SQLAlchemyProductImageRepository,
    SQLAlchemyProductRepository,
    SQLAlchemyProductReviewRepository,
    SQLAlchemyWishListRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[dict[str, Any], Depends(get_current_user)]
AdminDep = Annotated[dict[str, Any], Depends(require_role("admin", "super-admin"))]


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def _cat_repo(db: DbDep) -> SQLAlchemyProductCategoryRepository:
    return SQLAlchemyProductCategoryRepository(db)


def _brand_repo(db: DbDep) -> SQLAlchemyBrandRepository:
    return SQLAlchemyBrandRepository(db)


def _product_repo(db: DbDep) -> SQLAlchemyProductRepository:
    return SQLAlchemyProductRepository(db)


def _image_repo(db: DbDep) -> SQLAlchemyProductImageRepository:
    return SQLAlchemyProductImageRepository(db)


def _review_repo(db: DbDep) -> SQLAlchemyProductReviewRepository:
    return SQLAlchemyProductReviewRepository(db)


def _cart_repo(db: DbDep) -> SQLAlchemyCartRepository:
    return SQLAlchemyCartRepository(db)


def _wishlist_repo(db: DbDep) -> SQLAlchemyWishListRepository:
    return SQLAlchemyWishListRepository(db)


def _order_repo(db: DbDep) -> SQLAlchemyOrderRepository:
    return SQLAlchemyOrderRepository(db)


def _storage() -> LocalStorageAdapter:
    return LocalStorageAdapter()


# ---------------------------------------------------------------------------
# CATALOGUE PUBLIC
# ---------------------------------------------------------------------------


@router.get("/products", response_model=Page[ProductListSchema], tags=["Products"])
async def list_products(
    category_id: Annotated[int | None, Query(description="Filtrer par catégorie")] = None,
    brand_id: Annotated[int | None, Query(description="Filtrer par marque")] = None,
    search: Annotated[str | None, Query(description="Recherche textuelle")] = None,
    min_price: Annotated[Decimal | None, Query(description="Prix minimum")] = None,
    max_price: Annotated[Decimal | None, Query(description="Prix maximum")] = None,
    is_featured: Annotated[bool | None, Query(description="Produits mis en avant")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> Page[ProductListSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListProductsUseCase(repo)
    result = await uc.execute(
        params=params,
        category_id=category_id,
        brand_id=brand_id,
        search=search,
        min_price=min_price,
        max_price=max_price,
        is_featured=is_featured,
    )
    return result  # type: ignore[return-value]


@router.get("/products/{slug}", response_model=ProductDetailSchema, tags=["Products"])
async def get_product(
    slug: str,
    repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> ProductDetailSchema:
    uc = GetProductBySlugUseCase(repo)
    try:
        product = await uc.execute(slug)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProductDetailSchema.model_validate(product)


@router.get(
    "/product-categories",
    response_model=list[ProductCategorySchema],
    tags=["Categories"],
)
async def list_product_categories(
    repo: SQLAlchemyProductCategoryRepository = Depends(_cat_repo),
) -> list[ProductCategorySchema]:
    uc = ListCategoryTreeUseCase(repo)
    cats = await uc.execute()
    return [ProductCategorySchema.model_validate(c) for c in cats]


@router.get(
    "/product-categories/{slug}",
    response_model=ProductCategorySchema,
    tags=["Categories"],
)
async def get_product_category(
    slug: str,
    repo: SQLAlchemyProductCategoryRepository = Depends(_cat_repo),
) -> ProductCategorySchema:
    uc = GetCategoryBySlugUseCase(repo)
    try:
        cat = await uc.execute(slug)
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProductCategorySchema.model_validate(cat)


@router.get("/brands", response_model=list[BrandSchema], tags=["Brands"])
async def list_brands(
    repo: SQLAlchemyBrandRepository = Depends(_brand_repo),
) -> list[BrandSchema]:
    uc = ListBrandsUseCase(repo)
    brands = await uc.execute()
    return [BrandSchema.model_validate(b) for b in brands]


# ---------------------------------------------------------------------------
# AVIS PRODUITS
# ---------------------------------------------------------------------------


@router.get(
    "/products/{product_id}/reviews",
    response_model=Page[ProductReviewSchema],
    tags=["Reviews"],
)
async def list_product_reviews(
    product_id: int,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyProductReviewRepository = Depends(_review_repo),
) -> Page[ProductReviewSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListProductReviewsUseCase(repo)
    result = await uc.execute(product_id, params)
    return result  # type: ignore[return-value]


@router.post(
    "/products/{product_id}/reviews",
    response_model=ProductReviewSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Reviews"],
)
async def create_product_review(
    product_id: int,
    payload: ProductReviewCreateRequest,
    current_user: CurrentUserDep,
    repo: SQLAlchemyProductReviewRepository = Depends(_review_repo),
) -> ProductReviewSchema:
    uc = CreateReviewUseCase(repo)
    try:
        review = await uc.execute(
            product_id=product_id,
            user_id=current_user["id"],
            rating=payload.rating,
            comment=payload.comment,
        )
    except ReviewAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ProductReviewSchema.model_validate(review)


# ---------------------------------------------------------------------------
# PANIER
# ---------------------------------------------------------------------------


@router.get("/cart", response_model=CartSchema, tags=["Cart"])
async def get_cart(
    current_user: CurrentUserDep,
    repo: SQLAlchemyCartRepository = Depends(_cart_repo),
) -> CartSchema:
    uc = GetCartUseCase(repo)
    cart = await uc.execute(current_user["id"])
    return CartSchema.model_validate(cart)


@router.post(
    "/cart/items",
    response_model=CartSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Cart"],
)
async def add_to_cart(
    payload: AddToCartRequest,
    current_user: CurrentUserDep,
    cart_repo: SQLAlchemyCartRepository = Depends(_cart_repo),
    product_repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> CartSchema:
    uc = AddToCartUseCase(cart_repo, product_repo)
    try:
        cart = await uc.execute(
            user_id=current_user["id"],
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InsufficientStockError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return CartSchema.model_validate(cart)


@router.patch("/cart/items/{product_id}", response_model=CartSchema, tags=["Cart"])
async def update_cart_item(
    product_id: int,
    payload: UpdateCartItemRequest,
    current_user: CurrentUserDep,
    cart_repo: SQLAlchemyCartRepository = Depends(_cart_repo),
    product_repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> CartSchema:
    uc = UpdateCartItemUseCase(cart_repo, product_repo)
    try:
        cart = await uc.execute(
            user_id=current_user["id"],
            product_id=product_id,
            quantity=payload.quantity,
        )
    except CartItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InsufficientStockError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return CartSchema.model_validate(cart)


@router.delete("/cart/items/{product_id}", response_model=CartSchema, tags=["Cart"])
async def remove_from_cart(
    product_id: int,
    current_user: CurrentUserDep,
    repo: SQLAlchemyCartRepository = Depends(_cart_repo),
) -> CartSchema:
    uc = RemoveFromCartUseCase(repo)
    try:
        cart = await uc.execute(user_id=current_user["id"], product_id=product_id)
    except CartItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CartSchema.model_validate(cart)


@router.delete("/cart", response_model=CartSchema, tags=["Cart"])
async def clear_cart(
    current_user: CurrentUserDep,
    repo: SQLAlchemyCartRepository = Depends(_cart_repo),
) -> CartSchema:
    uc = ClearCartUseCase(repo)
    cart = await uc.execute(current_user["id"])
    return CartSchema.model_validate(cart)


# ---------------------------------------------------------------------------
# LISTE DE SOUHAITS
# ---------------------------------------------------------------------------


@router.get("/wishlist", response_model=WishListSchema, tags=["Wishlist"])
async def get_wishlist(
    current_user: CurrentUserDep,
    repo: SQLAlchemyWishListRepository = Depends(_wishlist_repo),
) -> WishListSchema:
    uc = GetWishListUseCase(repo)
    wl = await uc.execute(current_user["id"])
    return WishListSchema.model_validate(wl)


@router.post(
    "/wishlist/items",
    response_model=WishListSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Wishlist"],
)
async def add_to_wishlist(
    payload: AddToWishListRequest,
    current_user: CurrentUserDep,
    repo: SQLAlchemyWishListRepository = Depends(_wishlist_repo),
) -> WishListSchema:
    uc = AddToWishListUseCase(repo)
    try:
        wl = await uc.execute(user_id=current_user["id"], product_id=payload.product_id)
    except WishListItemAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return WishListSchema.model_validate(wl)


@router.delete("/wishlist/items/{product_id}", response_model=WishListSchema, tags=["Wishlist"])
async def remove_from_wishlist(
    product_id: int,
    current_user: CurrentUserDep,
    repo: SQLAlchemyWishListRepository = Depends(_wishlist_repo),
) -> WishListSchema:
    uc = RemoveFromWishListUseCase(repo)
    try:
        wl = await uc.execute(user_id=current_user["id"], product_id=product_id)
    except WishListItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return WishListSchema.model_validate(wl)


# ---------------------------------------------------------------------------
# COMMANDES
# ---------------------------------------------------------------------------


@router.post(
    "/orders",
    response_model=OrderSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Orders"],
)
async def create_order(
    payload: CreateOrderRequest,
    current_user: CurrentUserDep,
    cart_repo: SQLAlchemyCartRepository = Depends(_cart_repo),
    order_repo: SQLAlchemyOrderRepository = Depends(_order_repo),
    product_repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> OrderSchema:
    uc = CreateOrderUseCase(cart_repo, order_repo, product_repo)
    try:
        order = await uc.execute(
            user_id=current_user["id"],
            payment_gateway=payload.payment_gateway,
            shipping_address=payload.shipping_address,
            promotion_code=payload.promotion_code,
            notes=payload.notes,
        )
    except CartEmptyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (ProductNotFoundError, InsufficientStockError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return OrderSchema.model_validate(order)


@router.get("/orders", response_model=Page[OrderSchema], tags=["Orders"])
async def list_my_orders(
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    current_user: CurrentUserDep = None,  # type: ignore[assignment]
    repo: SQLAlchemyOrderRepository = Depends(_order_repo),
) -> Page[OrderSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListMyOrdersUseCase(repo)
    result = await uc.execute(
        user_id=current_user["id"], params=params, status=status_filter
    )
    return result  # type: ignore[return-value]


@router.get("/orders/{order_id}", response_model=OrderSchema, tags=["Orders"])
async def get_order(
    order_id: int,
    current_user: CurrentUserDep,
    repo: SQLAlchemyOrderRepository = Depends(_order_repo),
) -> OrderSchema:
    uc = GetOrderUseCase(repo)
    try:
        order = await uc.execute(order_id, user_id=current_user["id"])
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return OrderSchema.model_validate(order)


@router.post(
    "/orders/{order_id}/cancel",
    response_model=OrderSchema,
    tags=["Orders"],
)
async def cancel_order(
    order_id: int,
    current_user: CurrentUserDep,
    repo: SQLAlchemyOrderRepository = Depends(_order_repo),
) -> OrderSchema:
    uc = CancelOrderUseCase(repo)
    try:
        order = await uc.execute(order_id, user_id=current_user["id"])
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OrderCannotBeCancelledError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return OrderSchema.model_validate(order)


# ---------------------------------------------------------------------------
# ADMIN — Produits
# ---------------------------------------------------------------------------


@router.post(
    "/admin/products",
    response_model=ProductDetailSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin - Products"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_create_product(
    payload: ProductCreateRequest,
    current_user: AdminDep,
    repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> ProductDetailSchema:
    uc = CreateProductUseCase(repo)
    try:
        product = await uc.execute(
            vendor_id=payload.vendor_id,
            category_id=payload.category_id,
            brand_id=payload.brand_id,
            unit_id=payload.unit_id,
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            short_description=payload.short_description,
            price=payload.price,
            discount_price=payload.discount_price,
            stock_quantity=payload.stock_quantity,
            sku=payload.sku,
            is_active=payload.is_active,
            is_featured=payload.is_featured,
            weight=payload.weight,
            tax_id=payload.tax_id,
        )
    except SlugAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ProductDetailSchema.model_validate(product)


@router.put(
    "/admin/products/{product_id}",
    response_model=ProductDetailSchema,
    tags=["Admin - Products"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_product(
    product_id: int,
    payload: ProductUpdateRequest,
    repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> ProductDetailSchema:
    uc = UpdateProductUseCase(repo)
    try:
        product = await uc.execute(product_id=product_id, **payload.model_dump(exclude_none=True))
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProductDetailSchema.model_validate(product)


@router.delete(
    "/admin/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin - Products"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_product(
    product_id: int,
    repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> None:
    uc = DeleteProductUseCase(repo)
    try:
        await uc.execute(product_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/admin/products/{product_id}/toggle",
    response_model=ProductDetailSchema,
    tags=["Admin - Products"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_toggle_product(
    product_id: int,
    repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> ProductDetailSchema:
    uc = ToggleProductUseCase(repo)
    try:
        product = await uc.execute(product_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProductDetailSchema.model_validate(product)


@router.post(
    "/admin/products/{product_id}/images",
    response_model=ProductImageSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin - Products"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    is_primary: bool = False,
    sort_order: int = 0,
    image_repo: SQLAlchemyProductImageRepository = Depends(_image_repo),
    storage: LocalStorageAdapter = Depends(_storage),
) -> ProductImageSchema:
    uc = UploadProductImageUseCase(image_repo)
    content = await file.read()
    filename = file.filename or "upload"
    path = await storage.save(
        path=f"products/{product_id}/{filename}",
        content=content,
        content_type=file.content_type or "application/octet-stream",
    )
    img = await uc.execute(
        product_id=product_id,
        image_path=path,
        is_primary=is_primary,
        sort_order=sort_order,
    )
    return ProductImageSchema.model_validate(img)


@router.delete(
    "/admin/products/{product_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin - Products"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_product_image(
    product_id: int,
    image_id: int,
    repo: SQLAlchemyProductImageRepository = Depends(_image_repo),
) -> None:
    uc = DeleteProductImageUseCase(repo)
    try:
        await uc.execute(image_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# ADMIN — Catégories & Marques
# ---------------------------------------------------------------------------


@router.post(
    "/admin/product-categories",
    response_model=ProductCategorySchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin - Categories"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_create_category(
    payload: ProductCategoryCreateRequest,
    repo: SQLAlchemyProductCategoryRepository = Depends(_cat_repo),
) -> ProductCategorySchema:
    uc = CreateCategoryUseCase(repo)
    try:
        cat = await uc.execute(
            name=payload.name,
            slug=payload.slug,
            parent_id=payload.parent_id,
            image=payload.image,
            description=payload.description,
            is_active=payload.is_active,
            sort_order=payload.sort_order,
        )
    except SlugAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ProductCategorySchema.model_validate(cat)


@router.put(
    "/admin/product-categories/{category_id}",
    response_model=ProductCategorySchema,
    tags=["Admin - Categories"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_category(
    category_id: int,
    payload: ProductCategoryUpdateRequest,
    repo: SQLAlchemyProductCategoryRepository = Depends(_cat_repo),
) -> ProductCategorySchema:
    uc = UpdateCategoryUseCase(repo)
    try:
        cat = await uc.execute(category_id=category_id, **payload.model_dump(exclude_none=True))
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProductCategorySchema.model_validate(cat)


@router.delete(
    "/admin/product-categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin - Categories"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_category(
    category_id: int,
    repo: SQLAlchemyProductCategoryRepository = Depends(_cat_repo),
) -> None:
    uc = DeleteCategoryUseCase(repo)
    try:
        await uc.execute(category_id)
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/admin/brands",
    response_model=BrandSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin - Brands"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_create_brand(
    payload: BrandCreateRequest,
    repo: SQLAlchemyBrandRepository = Depends(_brand_repo),
) -> BrandSchema:
    uc = CreateBrandUseCase(repo)
    brand = await uc.execute(
        name=payload.name,
        slug=payload.slug,
        logo=payload.logo,
        description=payload.description,
        is_active=payload.is_active,
    )
    return BrandSchema.model_validate(brand)


@router.put(
    "/admin/brands/{brand_id}",
    response_model=BrandSchema,
    tags=["Admin - Brands"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_brand(
    brand_id: int,
    payload: BrandUpdateRequest,
    repo: SQLAlchemyBrandRepository = Depends(_brand_repo),
) -> BrandSchema:
    uc = UpdateBrandUseCase(repo)
    try:
        brand = await uc.execute(brand_id=brand_id, **payload.model_dump(exclude_none=True))
    except BrandNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BrandSchema.model_validate(brand)


@router.delete(
    "/admin/brands/{brand_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin - Brands"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_brand(
    brand_id: int,
    repo: SQLAlchemyBrandRepository = Depends(_brand_repo),
) -> None:
    uc = DeleteBrandUseCase(repo)
    try:
        await uc.execute(brand_id)
    except BrandNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# ADMIN — Commandes
# ---------------------------------------------------------------------------


@router.get(
    "/admin/orders",
    response_model=Page[OrderSchema],
    tags=["Admin - Orders"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_list_orders(
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    user_id: Annotated[int | None, Query()] = None,
    date_from: Annotated[str | None, Query()] = None,
    date_to: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyOrderRepository = Depends(_order_repo),
) -> Page[OrderSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListAllOrdersUseCase(repo)
    result = await uc.execute(
        params=params,
        status=status_filter,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
    )
    return result  # type: ignore[return-value]


@router.patch(
    "/admin/orders/{order_id}/status",
    response_model=OrderSchema,
    tags=["Admin - Orders"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_order_status(
    order_id: int,
    payload: UpdateOrderStatusRequest,
    repo: SQLAlchemyOrderRepository = Depends(_order_repo),
) -> OrderSchema:
    uc = UpdateOrderStatusUseCase(repo)
    try:
        order = await uc.execute(order_id, payload.status)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return OrderSchema.model_validate(order)


# ---------------------------------------------------------------------------
# ADMIN — Avis
# ---------------------------------------------------------------------------


@router.get(
    "/admin/reviews",
    response_model=Page[ProductReviewSchema],
    tags=["Admin - Reviews"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_list_pending_reviews(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyProductReviewRepository = Depends(_review_repo),
) -> Page[ProductReviewSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListPendingReviewsUseCase(repo)
    result = await uc.execute(params)
    return result  # type: ignore[return-value]


@router.patch(
    "/admin/reviews/{review_id}/approve",
    response_model=ProductReviewSchema,
    tags=["Admin - Reviews"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_approve_review(
    review_id: int,
    repo: SQLAlchemyProductReviewRepository = Depends(_review_repo),
) -> ProductReviewSchema:
    uc = ApproveReviewUseCase(repo)
    try:
        review = await uc.execute(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProductReviewSchema.model_validate(review)


@router.delete(
    "/admin/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin - Reviews"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_review(
    review_id: int,
    repo: SQLAlchemyProductReviewRepository = Depends(_review_repo),
) -> None:
    uc = DeleteReviewUseCase(repo)
    try:
        await uc.execute(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
