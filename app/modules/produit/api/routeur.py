"""Router FastAPI du module product (~42 endpoints)."""
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.core.storage.port import StoragePort
from app.core.storage.local_adapter import LocalStorageAdapter
from app.database import get_db
from app.modules.produit.api.schemas import (
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
from app.modules.produit.application.cas_utilisation import (
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
from app.modules.produit.domain.exceptions import (
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
from app.modules.produit.infrastructure.depots import (
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


@router.get("/produits", response_model=Page[ProductListSchema], tags=["Produits"])
async def list_products(
    id_categorie: Annotated[int | None, Query(description="Filtrer par catégorie")] = None,
    id_marque: Annotated[int | None, Query(description="Filtrer par marque")] = None,
    search: Annotated[str | None, Query(description="Recherche textuelle")] = None,
    min_price: Annotated[Decimal | None, Query(description="Prix minimum")] = None,
    max_price: Annotated[Decimal | None, Query(description="Prix maximum")] = None,
    est_mis_en_avant: Annotated[bool | None, Query(description="Produits mis en avant")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> Page[ProductListSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListProductsUseCase(repo)
    result = await uc.execute(
        params=params,
        id_categorie=id_categorie,
        id_marque=id_marque,
        search=search,
        min_price=min_price,
        max_price=max_price,
        est_mis_en_avant=est_mis_en_avant,
    )
    return result  # type: ignore[return-valeur]


@router.get("/produits/{identifiant_url}", response_model=ProductDetailSchema, tags=["Produits"])
async def get_product(
    identifiant_url: str,
    repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> ProductDetailSchema:
    uc = GetProductBySlugUseCase(repo)
    try:
        product = await uc.execute(identifiant_url)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProductDetailSchema.model_validate(product)


@router.get(
    "/categories-produits",
    response_model=list[ProductCategorySchema],
    tags=["Categories Produits"],
)
async def list_product_categories(
    repo: SQLAlchemyProductCategoryRepository = Depends(_cat_repo),
) -> list[ProductCategorySchema]:
    uc = ListCategoryTreeUseCase(repo)
    cats = await uc.execute()
    return [ProductCategorySchema.model_validate(c) for c in cats]


@router.get(
    "/categories-produits/{identifiant_url}",
    response_model=ProductCategorySchema,
    tags=["Categories Produits"],
)
async def get_product_category(
    identifiant_url: str,
    repo: SQLAlchemyProductCategoryRepository = Depends(_cat_repo),
) -> ProductCategorySchema:
    uc = GetCategoryBySlugUseCase(repo)
    try:
        cat = await uc.execute(identifiant_url)
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProductCategorySchema.model_validate(cat)


@router.get("/marques", response_model=list[BrandSchema], tags=["Marques"])
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
    "/produits/{id_produit}/avis",
    response_model=Page[ProductReviewSchema],
    tags=["Avis"],
)
async def list_product_reviews(
    id_produit: int,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyProductReviewRepository = Depends(_review_repo),
) -> Page[ProductReviewSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListProductReviewsUseCase(repo)
    result = await uc.execute(id_produit, params)
    return result  # type: ignore[return-valeur]


@router.post(
    "/produits/{id_produit}/avis",
    response_model=ProductReviewSchema,
    status_code=statut.HTTP_201_CREATED,
    tags=["Avis"],
)
async def create_product_review(
    id_produit: int,
    payload: ProductReviewCreateRequest,
    current_user: CurrentUserDep,
    repo: SQLAlchemyProductReviewRepository = Depends(_review_repo),
) -> ProductReviewSchema:
    uc = CreateReviewUseCase(repo)
    try:
        review = await uc.execute(
            id_produit=id_produit,
            id_utilisateur=current_user["id"],
            note=payload.note,
            commentaire=payload.commentaire,
        )
    except ReviewAlreadyExistsError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ProductReviewSchema.model_validate(review)


# ---------------------------------------------------------------------------
# PANIER
# ---------------------------------------------------------------------------


@router.get("/panier", response_model=CartSchema, tags=["Panier"])
async def get_cart(
    current_user: CurrentUserDep,
    repo: SQLAlchemyCartRepository = Depends(_cart_repo),
) -> CartSchema:
    uc = GetCartUseCase(repo)
    cart = await uc.execute(current_user["id"])
    return CartSchema.model_validate(cart)


@router.post(
    "/panier/articles",
    response_model=CartSchema,
    status_code=statut.HTTP_201_CREATED,
    tags=["Panier"],
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
            id_utilisateur=current_user["id"],
            id_produit=payload.id_produit,
            quantite=payload.quantite,
        )
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InsufficientStockError as exc:
        raise HTTPException(
            status_code=statut.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return CartSchema.model_validate(cart)


@router.patch("/panier/articles/{id_produit}", response_model=CartSchema, tags=["Panier"])
async def update_cart_item(
    id_produit: int,
    payload: UpdateCartItemRequest,
    current_user: CurrentUserDep,
    cart_repo: SQLAlchemyCartRepository = Depends(_cart_repo),
    product_repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> CartSchema:
    uc = UpdateCartItemUseCase(cart_repo, product_repo)
    try:
        cart = await uc.execute(
            id_utilisateur=current_user["id"],
            id_produit=id_produit,
            quantite=payload.quantite,
        )
    except CartItemNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InsufficientStockError as exc:
        raise HTTPException(
            status_code=statut.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return CartSchema.model_validate(cart)


@router.delete("/panier/articles/{id_produit}", response_model=CartSchema, tags=["Panier"])
async def remove_from_cart(
    id_produit: int,
    current_user: CurrentUserDep,
    repo: SQLAlchemyCartRepository = Depends(_cart_repo),
) -> CartSchema:
    uc = RemoveFromCartUseCase(repo)
    try:
        cart = await uc.execute(id_utilisateur=current_user["id"], id_produit=id_produit)
    except CartItemNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CartSchema.model_validate(cart)


@router.delete("/panier", response_model=CartSchema, tags=["Panier"])
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


@router.get("/liste-souhaits", response_model=WishListSchema, tags=["Liste de Souhaits"])
async def get_wishlist(
    current_user: CurrentUserDep,
    repo: SQLAlchemyWishListRepository = Depends(_wishlist_repo),
) -> WishListSchema:
    uc = GetWishListUseCase(repo)
    wl = await uc.execute(current_user["id"])
    return WishListSchema.model_validate(wl)


@router.post(
    "/liste-souhaits/articles",
    response_model=WishListSchema,
    status_code=statut.HTTP_201_CREATED,
    tags=["Liste de Souhaits"],
)
async def add_to_wishlist(
    payload: AddToWishListRequest,
    current_user: CurrentUserDep,
    repo: SQLAlchemyWishListRepository = Depends(_wishlist_repo),
) -> WishListSchema:
    uc = AddToWishListUseCase(repo)
    try:
        wl = await uc.execute(id_utilisateur=current_user["id"], id_produit=payload.id_produit)
    except WishListItemAlreadyExistsError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return WishListSchema.model_validate(wl)


@router.delete("/liste-souhaits/articles/{id_produit}", response_model=WishListSchema, tags=["Liste de Souhaits"])
async def remove_from_wishlist(
    id_produit: int,
    current_user: CurrentUserDep,
    repo: SQLAlchemyWishListRepository = Depends(_wishlist_repo),
) -> WishListSchema:
    uc = RemoveFromWishListUseCase(repo)
    try:
        wl = await uc.execute(id_utilisateur=current_user["id"], id_produit=id_produit)
    except WishListItemNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return WishListSchema.model_validate(wl)


# ---------------------------------------------------------------------------
# COMMANDES
# ---------------------------------------------------------------------------


@router.post(
    "/commandes",
    response_model=OrderSchema,
    status_code=statut.HTTP_201_CREATED,
    tags=["Commandes"],
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
            id_utilisateur=current_user["id"],
            passerelle_paiement=payload.passerelle_paiement,
            adresse_livraison=payload.adresse_livraison,
            promotion_code=payload.promotion_code,
            notes=payload.notes,
        )
    except CartEmptyError as exc:
        raise HTTPException(status_code=statut.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (ProductNotFoundError, InsufficientStockError) as exc:
        raise HTTPException(
            status_code=statut.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return OrderSchema.model_validate(order)


@router.get("/commandes", response_model=Page[OrderSchema], tags=["Commandes"])
async def list_my_orders(
    status_filter: Annotated[str | None, Query(alias="statut")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    current_user: CurrentUserDep = None,  # type: ignore[assignment]
    repo: SQLAlchemyOrderRepository = Depends(_order_repo),
) -> Page[OrderSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListMyOrdersUseCase(repo)
    result = await uc.execute(
        id_utilisateur=current_user["id"], params=params, statut=status_filter
    )
    return result  # type: ignore[return-valeur]


@router.get("/commandes/{id_commande}", response_model=OrderSchema, tags=["Commandes"])
async def get_order(
    id_commande: int,
    current_user: CurrentUserDep,
    repo: SQLAlchemyOrderRepository = Depends(_order_repo),
) -> OrderSchema:
    uc = GetOrderUseCase(repo)
    try:
        order = await uc.execute(id_commande, id_utilisateur=current_user["id"])
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return OrderSchema.model_validate(order)


@router.post(
    "/commandes/{id_commande}/annuler",
    response_model=OrderSchema,
    tags=["Commandes"],
)
async def cancel_order(
    id_commande: int,
    current_user: CurrentUserDep,
    repo: SQLAlchemyOrderRepository = Depends(_order_repo),
) -> OrderSchema:
    uc = CancelOrderUseCase(repo)
    try:
        order = await uc.execute(id_commande, id_utilisateur=current_user["id"])
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OrderCannotBeCancelledError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return OrderSchema.model_validate(order)


# ---------------------------------------------------------------------------
# ADMIN — Produits
# ---------------------------------------------------------------------------


@router.get(
    "/admin/produits",
    response_model=Page[ProductListSchema],
    tags=["Admin - Produits"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_list_products(
    search: Annotated[str | None, Query(description="Recherche textuelle")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> Page[ProductListSchema]:
    # Contrairement à GET /produits (public), inclut les produits désactivés :
    # sinon un produit désactivé disparaît de la liste admin et devient
    # impossible à réactiver depuis l'interface.
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListProductsUseCase(repo)
    result = await uc.execute(params=params, search=search, inclure_inactifs=True)
    return result  # type: ignore[return-valeur]


@router.post(
    "/admin/produits",
    response_model=ProductDetailSchema,
    status_code=statut.HTTP_201_CREATED,
    tags=["Admin - Produits"],
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
            id_prestataire=payload.id_prestataire,
            id_categorie=payload.id_categorie,
            id_marque=payload.id_marque,
            id_unite=payload.id_unite,
            nom=payload.nom,
            identifiant_url=payload.identifiant_url,
            description=payload.description,
            short_description=payload.short_description,
            prix=payload.prix,
            prix_remise=payload.prix_remise,
            quantite_stock=payload.quantite_stock,
            reference_article=payload.reference_article,
            est_actif=payload.est_actif,
            est_mis_en_avant=payload.est_mis_en_avant,
            poids=payload.poids,
            id_taxe=payload.id_taxe,
        )
    except SlugAlreadyExistsError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ProductDetailSchema.model_validate(product)


@router.put(
    "/admin/produits/{id_produit}",
    response_model=ProductDetailSchema,
    tags=["Admin - Produits"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_product(
    id_produit: int,
    payload: ProductUpdateRequest,
    repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> ProductDetailSchema:
    uc = UpdateProductUseCase(repo)
    try:
        product = await uc.execute(id_produit=id_produit, **payload.model_dump(exclude_none=True))
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProductDetailSchema.model_validate(product)


@router.delete(
    "/admin/produits/{id_produit}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    tags=["Admin - Produits"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_product(
    id_produit: int,
    repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> None:
    uc = DeleteProductUseCase(repo)
    try:
        await uc.execute(id_produit)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/admin/produits/{id_produit}/basculer",
    response_model=ProductDetailSchema,
    tags=["Admin - Produits"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_toggle_product(
    id_produit: int,
    repo: SQLAlchemyProductRepository = Depends(_product_repo),
) -> ProductDetailSchema:
    uc = ToggleProductUseCase(repo)
    try:
        product = await uc.execute(id_produit)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProductDetailSchema.model_validate(product)


@router.post(
    "/admin/produits/{id_produit}/images",
    response_model=ProductImageSchema,
    status_code=statut.HTTP_201_CREATED,
    tags=["Admin - Produits"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_upload_product_image(
    id_produit: int,
    file: UploadFile = File(...),
    est_principal: bool = False,
    ordre_affichage: int = 0,
    image_repo: SQLAlchemyProductImageRepository = Depends(_image_repo),
    storage: LocalStorageAdapter = Depends(_storage),
) -> ProductImageSchema:
    uc = UploadProductImageUseCase(image_repo)
    contenu = await file.read()
    filename = file.filename or "upload"
    path = await storage.save(
        path=f"products/{id_produit}/{filename}",
        contenu=contenu,
        content_type=file.content_type or "application/octet-stream",
    )
    img = await uc.execute(
        id_produit=id_produit,
        image_path=path,
        est_principal=est_principal,
        ordre_affichage=ordre_affichage,
    )
    return ProductImageSchema.model_validate(img)


@router.delete(
    "/admin/produits/{id_produit}/images/{image_id}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    tags=["Admin - Produits"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_product_image(
    id_produit: int,
    image_id: int,
    repo: SQLAlchemyProductImageRepository = Depends(_image_repo),
) -> None:
    uc = DeleteProductImageUseCase(repo)
    try:
        await uc.execute(image_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# ADMIN — Catégories & Marques
# ---------------------------------------------------------------------------


@router.post(
    "/admin/categories-produits",
    response_model=ProductCategorySchema,
    status_code=statut.HTTP_201_CREATED,
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
            nom=payload.nom,
            identifiant_url=payload.identifiant_url,
            id_parent=payload.id_parent,
            image=payload.image,
            description=payload.description,
            est_actif=payload.est_actif,
            ordre_affichage=payload.ordre_affichage,
        )
    except SlugAlreadyExistsError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ProductCategorySchema.model_validate(cat)


@router.put(
    "/admin/categories-produits/{id_categorie}",
    response_model=ProductCategorySchema,
    tags=["Admin - Categories"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_category(
    id_categorie: int,
    payload: ProductCategoryUpdateRequest,
    repo: SQLAlchemyProductCategoryRepository = Depends(_cat_repo),
) -> ProductCategorySchema:
    uc = UpdateCategoryUseCase(repo)
    try:
        cat = await uc.execute(id_categorie=id_categorie, **payload.model_dump(exclude_none=True))
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProductCategorySchema.model_validate(cat)


@router.delete(
    "/admin/categories-produits/{id_categorie}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    tags=["Admin - Categories"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_category(
    id_categorie: int,
    repo: SQLAlchemyProductCategoryRepository = Depends(_cat_repo),
) -> None:
    uc = DeleteCategoryUseCase(repo)
    try:
        await uc.execute(id_categorie)
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/admin/marques",
    response_model=BrandSchema,
    status_code=statut.HTTP_201_CREATED,
    tags=["Admin - Marques"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_create_brand(
    payload: BrandCreateRequest,
    repo: SQLAlchemyBrandRepository = Depends(_brand_repo),
) -> BrandSchema:
    uc = CreateBrandUseCase(repo)
    brand = await uc.execute(
        nom=payload.nom,
        identifiant_url=payload.identifiant_url,
        logo=payload.logo,
        description=payload.description,
        est_actif=payload.est_actif,
    )
    return BrandSchema.model_validate(brand)


@router.put(
    "/admin/marques/{id_marque}",
    response_model=BrandSchema,
    tags=["Admin - Marques"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_brand(
    id_marque: int,
    payload: BrandUpdateRequest,
    repo: SQLAlchemyBrandRepository = Depends(_brand_repo),
) -> BrandSchema:
    uc = UpdateBrandUseCase(repo)
    try:
        brand = await uc.execute(id_marque=id_marque, **payload.model_dump(exclude_none=True))
    except BrandNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BrandSchema.model_validate(brand)


@router.delete(
    "/admin/marques/{id_marque}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    tags=["Admin - Marques"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_brand(
    id_marque: int,
    repo: SQLAlchemyBrandRepository = Depends(_brand_repo),
) -> None:
    uc = DeleteBrandUseCase(repo)
    try:
        await uc.execute(id_marque)
    except BrandNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# ADMIN — Commandes
# ---------------------------------------------------------------------------


@router.get(
    "/admin/commandes",
    response_model=Page[OrderSchema],
    tags=["Admin - Commandes"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_list_orders(
    status_filter: Annotated[str | None, Query(alias="statut")] = None,
    id_utilisateur: Annotated[int | None, Query()] = None,
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
        statut=status_filter,
        id_utilisateur=id_utilisateur,
        date_from=date_from,
        date_to=date_to,
    )
    return result  # type: ignore[return-valeur]


@router.patch(
    "/admin/commandes/{id_commande}/statut",
    response_model=OrderSchema,
    tags=["Admin - Commandes"],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_order_status(
    id_commande: int,
    payload: UpdateOrderStatusRequest,
    repo: SQLAlchemyOrderRepository = Depends(_order_repo),
) -> OrderSchema:
    uc = UpdateOrderStatusUseCase(repo)
    try:
        order = await uc.execute(id_commande, payload.statut)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return OrderSchema.model_validate(order)


# ---------------------------------------------------------------------------
# ADMIN — Avis
# ---------------------------------------------------------------------------


@router.get(
    "/admin/avis",
    response_model=Page[ProductReviewSchema],
    tags=["Admin - Avis"],
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
    return result  # type: ignore[return-valeur]


@router.patch(
    "/admin/avis/{review_id}/approuver",
    response_model=ProductReviewSchema,
    tags=["Admin - Avis"],
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
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProductReviewSchema.model_validate(review)


@router.delete(
    "/admin/avis/{review_id}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    tags=["Admin - Avis"],
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
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
