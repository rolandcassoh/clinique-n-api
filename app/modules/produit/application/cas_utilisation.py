"""Use Cases du module product — application layer."""
import random
import string
from datetime import datetime
from decimal import Decimal

from app.modules.produit.domain.entites import (
    Brand,
    Cart,
    Order,
    Product,
    ProductCategory,
    ProductImage,
    ProductReview,
    WishList,
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
from app.modules.produit.domain.depots import (
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

    async def execute(self, identifiant_url: str) -> ProductCategory:
        cat = await self._repo.get_by_slug(identifiant_url)
        if cat is None:
            raise CategoryNotFoundError(identifiant_url)
        return cat


class CreateCategoryUseCase:
    def __init__(self, repo: ProductCategoryRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        nom: str,
        identifiant_url: str,
        id_parent: int | None,
        image: str | None,
        description: str | None,
        est_actif: bool,
        ordre_affichage: int,
    ) -> ProductCategory:
        existing = await self._repo.get_by_slug(identifiant_url)
        if existing is not None:
            raise SlugAlreadyExistsError(identifiant_url)
        return await self._repo.create(
            nom=nom,
            identifiant_url=identifiant_url,
            id_parent=id_parent,
            image=image,
            description=description,
            est_actif=est_actif,
            ordre_affichage=ordre_affichage,
        )


class UpdateCategoryUseCase:
    def __init__(self, repo: ProductCategoryRepository) -> None:
        self._repo = repo

    async def execute(self, id_categorie: int, **kwargs: object) -> ProductCategory:
        result = await self._repo.update(id_categorie=id_categorie, **kwargs)  # type: ignore[arg-type]
        if result is None:
            raise CategoryNotFoundError(id_categorie)
        return result


class DeleteCategoryUseCase:
    def __init__(self, repo: ProductCategoryRepository) -> None:
        self._repo = repo

    async def execute(self, id_categorie: int) -> None:
        deleted = await self._repo.soft_delete(id_categorie)
        if not deleted:
            raise CategoryNotFoundError(id_categorie)


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
        nom: str,
        identifiant_url: str,
        logo: str | None,
        description: str | None,
        est_actif: bool,
    ) -> Brand:
        return await self._repo.create(
            nom=nom, identifiant_url=identifiant_url, logo=logo, description=description, est_actif=est_actif
        )


class UpdateBrandUseCase:
    def __init__(self, repo: BrandRepository) -> None:
        self._repo = repo

    async def execute(self, id_marque: int, **kwargs: object) -> Brand:
        result = await self._repo.update(id_marque=id_marque, **kwargs)  # type: ignore[arg-type]
        if result is None:
            raise BrandNotFoundError(id_marque)
        return result


class DeleteBrandUseCase:
    def __init__(self, repo: BrandRepository) -> None:
        self._repo = repo

    async def execute(self, id_marque: int) -> None:
        deleted = await self._repo.soft_delete(id_marque)
        if not deleted:
            raise BrandNotFoundError(id_marque)


# ---------------------------------------------------------------------------
# Catalogue — Produits
# ---------------------------------------------------------------------------


class ListProductsUseCase:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        id_categorie: int | None = None,
        id_marque: int | None = None,
        search: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        est_mis_en_avant: bool | None = None,
    ) -> Page[Product]:
        products, total = await self._repo.list_paginated(
            params=params,
            id_categorie=id_categorie,
            id_marque=id_marque,
            search=search,
            min_price=min_price,
            max_price=max_price,
            est_mis_en_avant=est_mis_en_avant,
        )
        return Page.create(data=products, total=total, params=params)


class GetProductBySlugUseCase:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(self, identifiant_url: str) -> Product:
        product = await self._repo.get_by_slug(identifiant_url)
        if product is None:
            raise ProductNotFoundError(identifiant_url)
        return product


class CreateProductUseCase:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_prestataire: int,
        id_categorie: int,
        id_marque: int | None,
        id_unite: int | None,
        nom: str,
        identifiant_url: str,
        description: str | None,
        short_description: str | None,
        prix: Decimal,
        prix_remise: Decimal | None,
        quantite_stock: int,
        reference_article: str | None,
        est_actif: bool,
        est_mis_en_avant: bool,
        poids: Decimal | None,
        id_taxe: int | None,
    ) -> Product:
        existing = await self._repo.get_by_slug(identifiant_url)
        if existing is not None:
            raise SlugAlreadyExistsError(identifiant_url)
        return await self._repo.create(
            id_prestataire=id_prestataire,
            id_categorie=id_categorie,
            id_marque=id_marque,
            id_unite=id_unite,
            nom=nom,
            identifiant_url=identifiant_url,
            description=description,
            short_description=short_description,
            prix=prix,
            prix_remise=prix_remise,
            quantite_stock=quantite_stock,
            reference_article=reference_article,
            est_actif=est_actif,
            est_mis_en_avant=est_mis_en_avant,
            poids=poids,
            id_taxe=id_taxe,
        )


class UpdateProductUseCase:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(self, id_produit: int, **kwargs: object) -> Product:
        result = await self._repo.update(id_produit=id_produit, **kwargs)
        if result is None:
            raise ProductNotFoundError(id_produit)
        return result


class DeleteProductUseCase:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(self, id_produit: int) -> None:
        deleted = await self._repo.soft_delete(id_produit)
        if not deleted:
            raise ProductNotFoundError(id_produit)


class ToggleProductUseCase:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(self, id_produit: int) -> Product:
        result = await self._repo.toggle_active(id_produit)
        if result is None:
            raise ProductNotFoundError(id_produit)
        return result


class UploadProductImageUseCase:
    def __init__(self, repo: ProductImageRepository) -> None:
        self._repo = repo

    async def execute(
        self, id_produit: int, image_path: str, est_principal: bool, ordre_affichage: int
    ) -> ProductImage:
        return await self._repo.add_image(
            id_produit=id_produit,
            image=image_path,
            est_principal=est_principal,
            ordre_affichage=ordre_affichage,
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

    async def execute(self, id_produit: int, params: PaginationParams) -> Page[ProductReview]:
        reviews, total = await self._repo.list_approved(id_produit, params)
        return Page.create(data=reviews, total=total, params=params)


class CreateReviewUseCase:
    def __init__(self, repo: ProductReviewRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_produit: int,
        id_utilisateur: int,
        note: int,
        commentaire: str | None,
    ) -> ProductReview:
        already_exists = await self._repo.exists_for_user_product(id_utilisateur, id_produit)
        if already_exists:
            raise ReviewAlreadyExistsError(id_utilisateur, id_produit)
        return await self._repo.create(
            id_produit=id_produit, id_utilisateur=id_utilisateur, note=note, commentaire=commentaire
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

    async def execute(self, id_utilisateur: int) -> Cart:
        return await self._cart_repo.get_or_create(id_utilisateur)


class AddToCartUseCase:
    def __init__(self, cart_repo: CartRepository, product_repo: ProductRepository) -> None:
        self._cart_repo = cart_repo
        self._product_repo = product_repo

    async def execute(self, id_utilisateur: int, id_produit: int, quantite: int) -> Cart:
        product = await self._product_repo.get_by_id(id_produit)
        if product is None:
            raise ProductNotFoundError(id_produit)

        # Vérifie le stock
        if not product.has_enough_stock(quantite):
            raise InsufficientStockError(id_produit, quantite, product.quantite_stock)

        cart = await self._cart_repo.get_or_create(id_utilisateur)

        # Vérifie si cumulé la quantité existante ne dépasse pas le stock
        existing_item = cart.find_item(id_produit)
        if existing_item is not None:
            total_qty = existing_item.quantite + quantite
            if not product.has_enough_stock(total_qty):
                raise InsufficientStockError(id_produit, total_qty, product.quantite_stock)

        # prix_unitaire snapshotté au moment de l'ajout
        await self._cart_repo.add_or_update_item(
            id_panier=cart.id,
            id_produit=id_produit,
            quantite=quantite,
            prix_unitaire=product.effective_price,
        )
        return await self._cart_repo.get_or_create(id_utilisateur)


class UpdateCartItemUseCase:
    def __init__(self, cart_repo: CartRepository, product_repo: ProductRepository) -> None:
        self._cart_repo = cart_repo
        self._product_repo = product_repo

    async def execute(self, id_utilisateur: int, id_produit: int, quantite: int) -> Cart:
        cart = await self._cart_repo.get_or_create(id_utilisateur)
        item = cart.find_item(id_produit)
        if item is None:
            raise CartItemNotFoundError(id_produit)

        product = await self._product_repo.get_by_id(id_produit)
        if product and not product.has_enough_stock(quantite):
            raise InsufficientStockError(id_produit, quantite, product.quantite_stock)

        await self._cart_repo.update_item_quantity(
            id_panier=cart.id, id_produit=id_produit, quantite=quantite
        )
        return await self._cart_repo.get_or_create(id_utilisateur)


class RemoveFromCartUseCase:
    def __init__(self, cart_repo: CartRepository) -> None:
        self._cart_repo = cart_repo

    async def execute(self, id_utilisateur: int, id_produit: int) -> Cart:
        cart = await self._cart_repo.get_or_create(id_utilisateur)
        item = cart.find_item(id_produit)
        if item is None:
            raise CartItemNotFoundError(id_produit)
        await self._cart_repo.remove_item(id_panier=cart.id, id_produit=id_produit)
        return await self._cart_repo.get_or_create(id_utilisateur)


class ClearCartUseCase:
    def __init__(self, cart_repo: CartRepository) -> None:
        self._cart_repo = cart_repo

    async def execute(self, id_utilisateur: int) -> Cart:
        cart = await self._cart_repo.get_or_create(id_utilisateur)
        await self._cart_repo.clear(cart.id)
        return await self._cart_repo.get_or_create(id_utilisateur)


# ---------------------------------------------------------------------------
# Liste de souhaits
# ---------------------------------------------------------------------------


class GetWishListUseCase:
    def __init__(self, repo: WishListRepository) -> None:
        self._repo = repo

    async def execute(self, id_utilisateur: int) -> WishList:
        return await self._repo.get_or_create(id_utilisateur)


class AddToWishListUseCase:
    def __init__(self, repo: WishListRepository) -> None:
        self._repo = repo

    async def execute(self, id_utilisateur: int, id_produit: int) -> WishList:
        wl = await self._repo.get_or_create(id_utilisateur)
        added = await self._repo.add_item(wl.id, id_produit)
        if not added:
            raise WishListItemAlreadyExistsError(id_produit)
        return await self._repo.get_or_create(id_utilisateur)


class RemoveFromWishListUseCase:
    def __init__(self, repo: WishListRepository) -> None:
        self._repo = repo

    async def execute(self, id_utilisateur: int, id_produit: int) -> WishList:
        wl = await self._repo.get_or_create(id_utilisateur)
        removed = await self._repo.remove_item(wl.id, id_produit)
        if not removed:
            raise WishListItemNotFoundError(id_produit)
        return await self._repo.get_or_create(id_utilisateur)


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
    3. Calcule le sous_total
    4. Applique promotion (simplifiée — lookup via id_promotion si promotion_code fourni)
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
        id_utilisateur: int,
        passerelle_paiement: str | None,
        adresse_livraison: str | None,
        promotion_code: str | None,
        notes: str | None,
    ) -> Order:
        # 1. Récupérer le panier
        cart = await self._cart_repo.get_by_user_id(id_utilisateur)
        if cart is None or cart.is_empty():
            raise CartEmptyError()

        # 2. Valider le stock + construire les items
        order_items: list[dict] = []
        sous_total = Decimal("0")

        for cart_item in cart.items:
            product = await self._product_repo.get_by_id(cart_item.id_produit)
            if product is None:
                raise ProductNotFoundError(cart_item.id_produit)
            if not product.has_enough_stock(cart_item.quantite):
                raise InsufficientStockError(
                    cart_item.id_produit, cart_item.quantite, product.quantite_stock
                )
            item_subtotal = cart_item.prix_unitaire * cart_item.quantite
            sous_total += item_subtotal
            order_items.append(
                {
                    "id_produit": cart_item.id_produit,
                    "nom_produit": product.nom,
                    "prix_unitaire": cart_item.prix_unitaire,
                    "quantite": cart_item.quantite,
                    "sous_total": item_subtotal,
                }
            )

        # 3. Calcul taxes (simplifiée à 0)
        montant_taxe = Decimal("0")

        # 4. Remise (simplifiée — pas de table promotions branchée ici)
        montant_remise = Decimal("0")

        # 5. Shipping (simplifiée à 0)
        frais_livraison = Decimal("0")

        total = sous_total + montant_taxe + frais_livraison - montant_remise

        # 6. Référence unique
        reference = _generate_order_reference()

        # 7. Créer la commande
        order = await self._order_repo.create(
            reference=reference,
            id_utilisateur=id_utilisateur,
            id_prestataire=None,
            sous_total=sous_total,
            montant_remise=montant_remise,
            montant_taxe=montant_taxe,
            frais_livraison=frais_livraison,
            total=total,
            passerelle_paiement=passerelle_paiement,
            adresse_livraison=adresse_livraison,
            notes=notes,
            id_promotion=None,
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
        id_utilisateur: int,
        params: PaginationParams,
        statut: str | None = None,
    ) -> Page[Order]:
        orders, total = await self._repo.list_for_user(id_utilisateur, params, statut)
        return Page.create(data=orders, total=total, params=params)


class GetOrderUseCase:
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def execute(self, id_commande: int, id_utilisateur: int | None = None) -> Order:
        order = await self._repo.get_by_id(id_commande)
        if order is None:
            raise OrderNotFoundError(id_commande)
        # Si id_utilisateur fourni, vérifier que la commande appartient bien à l'utilisateur
        if id_utilisateur is not None and order.id_utilisateur != id_utilisateur:
            raise OrderNotFoundError(id_commande)
        return order


class CancelOrderUseCase:
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def execute(self, id_commande: int, id_utilisateur: int | None = None) -> Order:
        order = await self._repo.get_by_id(id_commande)
        if order is None:
            raise OrderNotFoundError(id_commande)
        if id_utilisateur is not None and order.id_utilisateur != id_utilisateur:
            raise OrderNotFoundError(id_commande)
        if not order.can_cancel():
            raise OrderCannotBeCancelledError(id_commande, order.statut)
        result = await self._repo.cancel(id_commande)
        if result is None:
            raise OrderNotFoundError(id_commande)
        return result


class ListAllOrdersUseCase:
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        statut: str | None = None,
        id_utilisateur: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> Page[Order]:
        orders, total = await self._repo.list_all(
            params=params,
            statut=statut,
            id_utilisateur=id_utilisateur,
            date_from=date_from,
            date_to=date_to,
        )
        return Page.create(data=orders, total=total, params=params)


class UpdateOrderStatusUseCase:
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def execute(self, id_commande: int, new_status: str) -> Order:
        result = await self._repo.update_status(id_commande, new_status)
        if result is None:
            raise OrderNotFoundError(id_commande)
        return result
