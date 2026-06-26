"""Implémentations SQLAlchemy async des repositories du module product."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.produit.domain.entites import (
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
from app.modules.produit.domain.depots import (
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
from app.modules.produit.infrastructure.modeles import (
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
        nom=m.nom,
        identifiant_url=m.identifiant_url,
        id_parent=m.id_parent,
        image=m.image,
        description=m.description,
        est_actif=m.est_actif,
        ordre_affichage=m.ordre_affichage,
        children=children or [],
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _brand_to_entity(m: BrandModel) -> Brand:
    return Brand(
        id=m.id,
        nom=m.nom,
        identifiant_url=m.identifiant_url,
        logo=m.logo,
        description=m.description,
        est_actif=m.est_actif,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _unit_to_entity(m: UnitModel) -> Unit:
    return Unit(
        id=m.id,
        nom=m.nom,
        abréviation=m.abréviation,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _image_to_entity(m: ProductImageModel) -> ProductImage:
    return ProductImage(
        id=m.id,
        id_produit=m.id_produit,
        image=m.image,
        est_principal=m.est_principal,
        ordre_affichage=m.ordre_affichage,
        created_at=m.created_at or datetime.now(),
        updated_at=m.updated_at or datetime.now(),
    )


def _product_to_entity(m: ProductModel) -> Product:
    images = [_image_to_entity(img) for img in (m.images or [])]
    return Product(
        id=m.id,
        id_prestataire=m.id_prestataire,
        id_categorie=m.id_categorie,
        id_marque=m.id_marque,
        id_unite=m.id_unite,
        nom=m.nom,
        identifiant_url=m.identifiant_url,
        description=m.description,
        short_description=m.short_description,
        prix=m.prix,
        prix_remise=m.prix_remise,
        quantite_stock=m.quantite_stock,
        reference_article=m.reference_article,
        est_actif=m.est_actif,
        est_mis_en_avant=m.est_mis_en_avant,
        poids=m.poids,
        id_taxe=m.id_taxe,
        category_name=m.category.nom if m.category else None,
        brand_name=m.brand.nom if m.brand else None,
        unit_name=m.unit.nom if m.unit else None,
        images=images,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _review_to_entity(m: ProductReviewModel) -> ProductReview:
    return ProductReview(
        id=m.id,
        id_produit=m.id_produit,
        id_utilisateur=m.id_utilisateur,
        note=m.note,
        commentaire=m.commentaire,
        est_approuve=m.est_approuve,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _cart_item_to_entity(m: CartItemModel) -> CartItem:
    product = m.product
    primary_image: str | None = None
    if product and product.images:
        primaries = [img for img in product.images if img.est_principal]
        primary_image = primaries[0].image if primaries else product.images[0].image
    return CartItem(
        id=m.id,
        id_panier=m.id_panier,
        id_produit=m.id_produit,
        quantite=m.quantite,
        prix_unitaire=m.prix_unitaire,
        nom_produit=product.nom if product else None,
        product_image=primary_image,
        created_at=m.created_at or datetime.now(),
        updated_at=m.updated_at or datetime.now(),
    )


def _cart_to_entity(m: CartModel) -> Cart:
    return Cart(
        id=m.id,
        id_utilisateur=m.id_utilisateur,
        items=[_cart_item_to_entity(i) for i in (m.items or [])],
        created_at=m.created_at or datetime.now(),
        updated_at=m.updated_at or datetime.now(),
    )


def _wishlist_item_to_entity(m: WishListItemModel) -> WishListItem:
    product = m.product
    primary_image: str | None = None
    if product and product.images:
        primaries = [img for img in product.images if img.est_principal]
        primary_image = primaries[0].image if primaries else product.images[0].image
    return WishListItem(
        id=m.id,
        id_liste_souhaits=m.id_liste_souhaits,
        id_produit=m.id_produit,
        nom_produit=product.nom if product else None,
        product_image=primary_image,
        product_price=product.prix if product else None,
        created_at=m.created_at or datetime.now(),
        updated_at=m.updated_at or datetime.now(),
    )


def _wishlist_to_entity(m: WishListModel) -> WishList:
    return WishList(
        id=m.id,
        id_utilisateur=m.id_utilisateur,
        items=[_wishlist_item_to_entity(i) for i in (m.items or [])],
        created_at=m.created_at or datetime.now(),
        updated_at=m.updated_at or datetime.now(),
    )


def _order_item_to_entity(m: OrderItemModel) -> OrderItem:
    return OrderItem(
        id=m.id,
        id_commande=m.id_commande,
        id_produit=m.id_produit,
        nom_produit=m.nom_produit,
        prix_unitaire=m.prix_unitaire,
        quantite=m.quantite,
        sous_total=m.sous_total,
        created_at=m.created_at or datetime.now(),
        updated_at=m.updated_at or datetime.now(),
    )


def _order_to_entity(m: OrderModel) -> Order:
    return Order(
        id=m.id,
        reference=m.reference,
        id_utilisateur=m.id_utilisateur,
        id_prestataire=m.id_prestataire,
        sous_total=m.sous_total,
        montant_remise=m.montant_remise,
        montant_taxe=m.montant_taxe,
        frais_livraison=m.frais_livraison,
        total=m.total,
        statut=m.statut,
        statut_paiement=m.statut_paiement,
        passerelle_paiement=m.passerelle_paiement,
        adresse_livraison=m.adresse_livraison,
        notes=m.notes,
        id_promotion=m.id_promotion,
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
                ProductCategoryModel.est_actif.is_(True),
            )
            .order_by(ProductCategoryModel.ordre_affichage)
        )
        lignes = (await self._session.execute(q)).scalars().all()

        # Construit l'arbre en mémoire
        par_id: dict[int, ProductCategory] = {}
        for ligne in lignes:
            par_id[ligne.id] = _cat_to_entity(ligne)

        racines: list[ProductCategory] = []
        for ligne in lignes:
            entite = par_id[ligne.id]
            if ligne.id_parent is None:
                racines.append(entite)
            elif ligne.id_parent in par_id:
                par_id[ligne.id_parent].children.append(entite)

        return racines

    async def get_by_slug(self, identifiant_url: str) -> ProductCategory | None:
        q = select(ProductCategoryModel).where(
            ProductCategoryModel.identifiant_url == identifiant_url,
            ProductCategoryModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        return _cat_to_entity(ligne) if ligne else None

    async def get_by_id(self, id_categorie: int) -> ProductCategory | None:
        q = select(ProductCategoryModel).where(
            ProductCategoryModel.id == id_categorie,
            ProductCategoryModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        return _cat_to_entity(ligne) if ligne else None

    async def create(
        self,
        nom: str,
        identifiant_url: str,
        id_parent: int | None,
        image: str | None,
        description: str | None,
        est_actif: bool,
        ordre_affichage: int,
    ) -> ProductCategory:
        categorie = ProductCategoryModel(
            nom=nom,
            identifiant_url=identifiant_url,
            id_parent=id_parent,
            image=image,
            description=description,
            est_actif=est_actif,
            ordre_affichage=ordre_affichage,
        )
        self._session.add(categorie)
        await self._session.flush()
        await self._session.refresh(categorie)
        return _cat_to_entity(categorie)

    async def update(
        self,
        id_categorie: int,
        nom: str | None,
        identifiant_url: str | None,
        id_parent: int | None,
        image: str | None,
        description: str | None,
        est_actif: bool | None,
        ordre_affichage: int | None,
    ) -> ProductCategory | None:
        q = select(ProductCategoryModel).where(
            ProductCategoryModel.id == id_categorie,
            ProductCategoryModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return None
        if nom is not None:
            ligne.nom = nom
        if identifiant_url is not None:
            ligne.identifiant_url = identifiant_url
        if id_parent is not None:
            ligne.id_parent = id_parent
        if image is not None:
            ligne.image = image
        if description is not None:
            ligne.description = description
        if est_actif is not None:
            ligne.est_actif = est_actif
        if ordre_affichage is not None:
            ligne.ordre_affichage = ordre_affichage
        await self._session.flush()
        await self._session.refresh(ligne)
        return _cat_to_entity(ligne)

    async def soft_delete(self, id_categorie: int) -> bool:
        q = select(ProductCategoryModel).where(
            ProductCategoryModel.id == id_categorie,
            ProductCategoryModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return False
        ligne.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True


class SQLAlchemyBrandRepository(BrandRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[Brand]:
        q = (
            select(BrandModel)
            .where(BrandModel.deleted_at.is_(None), BrandModel.est_actif.is_(True))
            .order_by(BrandModel.nom)
        )
        lignes = (await self._session.execute(q)).scalars().all()
        return [_brand_to_entity(r) for r in lignes]

    async def get_by_id(self, id_marque: int) -> Brand | None:
        q = select(BrandModel).where(
            BrandModel.id == id_marque, BrandModel.deleted_at.is_(None)
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        return _brand_to_entity(ligne) if ligne else None

    async def create(
        self,
        nom: str,
        identifiant_url: str,
        logo: str | None,
        description: str | None,
        est_actif: bool,
    ) -> Brand:
        marque = BrandModel(
            nom=nom, identifiant_url=identifiant_url, logo=logo, description=description, est_actif=est_actif
        )
        self._session.add(marque)
        await self._session.flush()
        await self._session.refresh(marque)
        return _brand_to_entity(marque)

    async def update(
        self,
        id_marque: int,
        nom: str | None,
        identifiant_url: str | None,
        logo: str | None,
        description: str | None,
        est_actif: bool | None,
    ) -> Brand | None:
        q = select(BrandModel).where(
            BrandModel.id == id_marque, BrandModel.deleted_at.is_(None)
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return None
        if nom is not None:
            ligne.nom = nom
        if identifiant_url is not None:
            ligne.identifiant_url = identifiant_url
        if logo is not None:
            ligne.logo = logo
        if description is not None:
            ligne.description = description
        if est_actif is not None:
            ligne.est_actif = est_actif
        await self._session.flush()
        await self._session.refresh(ligne)
        return _brand_to_entity(ligne)

    async def soft_delete(self, id_marque: int) -> bool:
        q = select(BrandModel).where(
            BrandModel.id == id_marque, BrandModel.deleted_at.is_(None)
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return False
        ligne.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True


class SQLAlchemyUnitRepository(UnitRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id_unite: int) -> Unit | None:
        q = select(UnitModel).where(
            UnitModel.id == id_unite, UnitModel.deleted_at.is_(None)
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        return _unit_to_entity(ligne) if ligne else None


class SQLAlchemyProductRepository(ProductRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_paginated(
        self,
        params: PaginationParams,
        id_categorie: int | None = None,
        id_marque: int | None = None,
        search: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        est_mis_en_avant: bool | None = None,
    ) -> tuple[list[Product], int]:
        base_q = select(ProductModel).where(
            ProductModel.deleted_at.is_(None),
            ProductModel.est_actif.is_(True),
        )
        if id_categorie is not None:
            base_q = base_q.where(ProductModel.id_categorie == id_categorie)
        if id_marque is not None:
            base_q = base_q.where(ProductModel.id_marque == id_marque)
        if search:
            base_q = base_q.where(
                ProductModel.nom.ilike(f"%{search}%")
                | ProductModel.short_description.ilike(f"%{search}%")
            )
        if min_price is not None:
            base_q = base_q.where(ProductModel.prix >= min_price)
        if max_price is not None:
            base_q = base_q.where(ProductModel.prix <= max_price)
        if est_mis_en_avant is not None:
            base_q = base_q.where(ProductModel.est_mis_en_avant == est_mis_en_avant)

        requete_compte = select(func.count()).select_from(base_q.subquery())
        total: int = (await self._session.execute(requete_compte)).scalar_one()

        requete_lignes = (
            base_q.order_by(ProductModel.created_at.desc())
            .offset(params.offset)
            .limit(params.per_page)
        )
        lignes = (await self._session.execute(requete_lignes)).scalars().all()
        return [_product_to_entity(r) for r in lignes], total

    async def get_by_slug(self, identifiant_url: str) -> Product | None:
        q = select(ProductModel).where(
            ProductModel.identifiant_url == identifiant_url, ProductModel.deleted_at.is_(None)
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        return _product_to_entity(ligne) if ligne else None

    async def get_by_id(self, id_produit: int) -> Product | None:
        q = select(ProductModel).where(
            ProductModel.id == id_produit, ProductModel.deleted_at.is_(None)
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        return _product_to_entity(ligne) if ligne else None

    async def create(
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
        product = ProductModel(
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
        self._session.add(product)
        await self._session.flush()
        await self._session.refresh(product)
        return _product_to_entity(product)

    async def update(self, id_produit: int, **kwargs: object) -> Product | None:
        q = select(ProductModel).where(
            ProductModel.id == id_produit, ProductModel.deleted_at.is_(None)
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return None
        for nom_champ, valeur in kwargs.items():
            if valeur is not None and hasattr(ligne, nom_champ):
                setattr(ligne, nom_champ, valeur)
        await self._session.flush()
        await self._session.refresh(ligne)
        return _product_to_entity(ligne)

    async def soft_delete(self, id_produit: int) -> bool:
        q = select(ProductModel).where(
            ProductModel.id == id_produit, ProductModel.deleted_at.is_(None)
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return False
        ligne.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True

    async def toggle_active(self, id_produit: int) -> Product | None:
        q = select(ProductModel).where(
            ProductModel.id == id_produit, ProductModel.deleted_at.is_(None)
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return None
        ligne.est_actif = not ligne.est_actif
        await self._session.flush()
        await self._session.refresh(ligne)
        return _product_to_entity(ligne)


class SQLAlchemyProductImageRepository(ProductImageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_image(
        self,
        id_produit: int,
        image: str,
        est_principal: bool,
        ordre_affichage: int,
    ) -> ProductImage:
        img = ProductImageModel(
            id_produit=id_produit,
            image=image,
            est_principal=est_principal,
            ordre_affichage=ordre_affichage,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self._session.add(img)
        await self._session.flush()
        await self._session.refresh(img)
        return _image_to_entity(img)

    async def delete_image(self, image_id: int) -> bool:
        q = select(ProductImageModel).where(ProductImageModel.id == image_id)
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return False
        await self._session.delete(ligne)
        await self._session.flush()
        return True

    async def list_for_product(self, id_produit: int) -> list[ProductImage]:
        q = (
            select(ProductImageModel)
            .where(ProductImageModel.id_produit == id_produit)
            .order_by(ProductImageModel.ordre_affichage)
        )
        lignes = (await self._session.execute(q)).scalars().all()
        return [_image_to_entity(r) for r in lignes]


class SQLAlchemyProductReviewRepository(ProductReviewRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_approved(
        self, id_produit: int, params: PaginationParams
    ) -> tuple[list[ProductReview], int]:
        requete_base = select(ProductReviewModel).where(
            ProductReviewModel.id_produit == id_produit,
            ProductReviewModel.est_approuve.is_(True),
            ProductReviewModel.deleted_at.is_(None),
        )
        total: int = (
            await self._session.execute(
                select(func.count()).select_from(requete_base.subquery())
            )
        ).scalar_one()
        lignes = (
            await self._session.execute(
                requete_base.order_by(ProductReviewModel.created_at.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_review_to_entity(r) for r in lignes], total

    async def list_pending(
        self, params: PaginationParams
    ) -> tuple[list[ProductReview], int]:
        requete_base = select(ProductReviewModel).where(
            ProductReviewModel.est_approuve.is_(False),
            ProductReviewModel.deleted_at.is_(None),
        )
        total: int = (
            await self._session.execute(
                select(func.count()).select_from(requete_base.subquery())
            )
        ).scalar_one()
        lignes = (
            await self._session.execute(
                requete_base.order_by(ProductReviewModel.created_at.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_review_to_entity(r) for r in lignes], total

    async def get_by_id(self, review_id: int) -> ProductReview | None:
        q = select(ProductReviewModel).where(
            ProductReviewModel.id == review_id,
            ProductReviewModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        return _review_to_entity(ligne) if ligne else None

    async def exists_for_user_product(self, id_utilisateur: int, id_produit: int) -> bool:
        q = select(func.count()).where(
            ProductReviewModel.id_utilisateur == id_utilisateur,
            ProductReviewModel.id_produit == id_produit,
            ProductReviewModel.deleted_at.is_(None),
        )
        nombre: int = (await self._session.execute(q)).scalar_one()
        return nombre > 0

    async def create(
        self,
        id_produit: int,
        id_utilisateur: int,
        note: int,
        commentaire: str | None,
    ) -> ProductReview:
        review = ProductReviewModel(
            id_produit=id_produit,
            id_utilisateur=id_utilisateur,
            note=note,
            commentaire=commentaire,
            est_approuve=False,
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
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return None
        ligne.est_approuve = True
        await self._session.flush()
        await self._session.refresh(ligne)
        return _review_to_entity(ligne)

    async def soft_delete(self, review_id: int) -> bool:
        q = select(ProductReviewModel).where(
            ProductReviewModel.id == review_id,
            ProductReviewModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return False
        ligne.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True


class SQLAlchemyCartRepository(CartRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _load_cart(self, id_panier: int) -> CartModel | None:
        q = select(CartModel).where(CartModel.id == id_panier)
        return (await self._session.execute(q)).scalar_one_or_none()

    async def get_or_create(self, id_utilisateur: int) -> Cart:
        q = select(CartModel).where(CartModel.id_utilisateur == id_utilisateur)
        cart = (await self._session.execute(q)).scalar_one_or_none()
        if cart is None:
            now = datetime.utcnow()
            cart = CartModel(id_utilisateur=id_utilisateur, created_at=now, updated_at=now)
            self._session.add(cart)
            await self._session.flush()
            await self._session.refresh(cart)
        return _cart_to_entity(cart)

    async def get_by_user_id(self, id_utilisateur: int) -> Cart | None:
        q = select(CartModel).where(CartModel.id_utilisateur == id_utilisateur)
        cart = (await self._session.execute(q)).scalar_one_or_none()
        return _cart_to_entity(cart) if cart else None

    async def add_or_update_item(
        self,
        id_panier: int,
        id_produit: int,
        quantite: int,
        prix_unitaire: Decimal,
    ) -> CartItem:
        # Cherche si l'article existe déjà dans le panier
        q = select(CartItemModel).where(
            CartItemModel.id_panier == id_panier,
            CartItemModel.id_produit == id_produit,
        )
        existant = (await self._session.execute(q)).scalar_one_or_none()
        maintenant = datetime.utcnow()
        if existant is not None:
            # Additionne les quantités (règle métier)
            existant.quantite += quantite
            existant.updated_at = maintenant
            await self._session.flush()
            await self._session.refresh(existant)
            return _cart_item_to_entity(existant)
        else:
            article = CartItemModel(
                id_panier=id_panier,
                id_produit=id_produit,
                quantite=quantite,
                prix_unitaire=prix_unitaire,
                created_at=maintenant,
                updated_at=maintenant,
            )
            self._session.add(article)
            await self._session.flush()
            await self._session.refresh(article)
            return _cart_item_to_entity(article)

    async def update_item_quantity(
        self,
        id_panier: int,
        id_produit: int,
        quantite: int,
    ) -> CartItem | None:
        q = select(CartItemModel).where(
            CartItemModel.id_panier == id_panier,
            CartItemModel.id_produit == id_produit,
        )
        article = (await self._session.execute(q)).scalar_one_or_none()
        if article is None:
            return None
        article.quantite = quantite
        article.updated_at = datetime.utcnow()
        await self._session.flush()
        await self._session.refresh(article)
        return _cart_item_to_entity(article)

    async def remove_item(self, id_panier: int, id_produit: int) -> bool:
        q = select(CartItemModel).where(
            CartItemModel.id_panier == id_panier,
            CartItemModel.id_produit == id_produit,
        )
        article = (await self._session.execute(q)).scalar_one_or_none()
        if article is None:
            return False
        await self._session.delete(article)
        await self._session.flush()
        return True

    async def clear(self, id_panier: int) -> None:
        q = select(CartItemModel).where(CartItemModel.id_panier == id_panier)
        articles = (await self._session.execute(q)).scalars().all()
        for article in articles:
            await self._session.delete(article)
        await self._session.flush()


class SQLAlchemyWishListRepository(WishListRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self, id_utilisateur: int) -> WishList:
        q = select(WishListModel).where(WishListModel.id_utilisateur == id_utilisateur)
        wl = (await self._session.execute(q)).scalar_one_or_none()
        if wl is None:
            now = datetime.utcnow()
            wl = WishListModel(id_utilisateur=id_utilisateur, created_at=now, updated_at=now)
            self._session.add(wl)
            await self._session.flush()
            await self._session.refresh(wl)
        return _wishlist_to_entity(wl)

    async def add_item(self, id_liste_souhaits: int, id_produit: int) -> bool:
        q = select(WishListItemModel).where(
            WishListItemModel.id_liste_souhaits == id_liste_souhaits,
            WishListItemModel.id_produit == id_produit,
        )
        existant = (await self._session.execute(q)).scalar_one_or_none()
        if existant is not None:
            return False
        maintenant = datetime.utcnow()
        element = WishListItemModel(
            id_liste_souhaits=id_liste_souhaits,
            id_produit=id_produit,
            created_at=maintenant,
            updated_at=maintenant,
        )
        self._session.add(element)
        await self._session.flush()
        return True

    async def remove_item(self, id_liste_souhaits: int, id_produit: int) -> bool:
        q = select(WishListItemModel).where(
            WishListItemModel.id_liste_souhaits == id_liste_souhaits,
            WishListItemModel.id_produit == id_produit,
        )
        element = (await self._session.execute(q)).scalar_one_or_none()
        if element is None:
            return False
        await self._session.delete(element)
        await self._session.flush()
        return True


class SQLAlchemyOrderRepository(OrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        reference: str,
        id_utilisateur: int,
        id_prestataire: int | None,
        sous_total: Decimal,
        montant_remise: Decimal,
        montant_taxe: Decimal,
        frais_livraison: Decimal,
        total: Decimal,
        passerelle_paiement: str | None,
        adresse_livraison: str | None,
        notes: str | None,
        id_promotion: int | None,
        items: list[dict],
    ) -> Order:
        now = datetime.utcnow()
        order = OrderModel(
            reference=reference,
            id_utilisateur=id_utilisateur,
            id_prestataire=id_prestataire,
            sous_total=sous_total,
            montant_remise=montant_remise,
            montant_taxe=montant_taxe,
            frais_livraison=frais_livraison,
            total=total,
            passerelle_paiement=passerelle_paiement,
            adresse_livraison=adresse_livraison,
            notes=notes,
            id_promotion=id_promotion,
            statut="pending",
            statut_paiement="pending",
        )
        self._session.add(order)
        await self._session.flush()

        for donnees_article in items:
            ligne_commande = OrderItemModel(
                id_commande=order.id,
                id_produit=donnees_article["id_produit"],
                nom_produit=donnees_article["nom_produit"],
                prix_unitaire=donnees_article["prix_unitaire"],
                quantite=donnees_article["quantite"],
                sous_total=donnees_article["sous_total"],
                created_at=now,
                updated_at=now,
            )
            self._session.add(ligne_commande)

        await self._session.flush()
        await self._session.refresh(order)
        return _order_to_entity(order)

    async def list_for_user(
        self,
        id_utilisateur: int,
        params: PaginationParams,
        statut: str | None = None,
    ) -> tuple[list[Order], int]:
        requete_base = select(OrderModel).where(
            OrderModel.id_utilisateur == id_utilisateur,
            OrderModel.deleted_at.is_(None),
        )
        if statut:
            requete_base = requete_base.where(OrderModel.statut == statut)
        total: int = (
            await self._session.execute(
                select(func.count()).select_from(requete_base.subquery())
            )
        ).scalar_one()
        lignes = (
            await self._session.execute(
                requete_base.order_by(OrderModel.created_at.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_order_to_entity(r) for r in lignes], total

    async def list_all(
        self,
        params: PaginationParams,
        statut: str | None = None,
        id_utilisateur: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[list[Order], int]:
        requete_base = select(OrderModel).where(OrderModel.deleted_at.is_(None))
        if statut:
            requete_base = requete_base.where(OrderModel.statut == statut)
        if id_utilisateur:
            requete_base = requete_base.where(OrderModel.id_utilisateur == id_utilisateur)
        if date_from:
            requete_base = requete_base.where(OrderModel.created_at >= date_from)
        if date_to:
            requete_base = requete_base.where(OrderModel.created_at <= date_to)
        total: int = (
            await self._session.execute(
                select(func.count()).select_from(requete_base.subquery())
            )
        ).scalar_one()
        lignes = (
            await self._session.execute(
                requete_base.order_by(OrderModel.created_at.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_order_to_entity(r) for r in lignes], total

    async def get_by_id(self, id_commande: int) -> Order | None:
        q = select(OrderModel).where(
            OrderModel.id == id_commande,
            OrderModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        return _order_to_entity(ligne) if ligne else None

    async def update_status(self, id_commande: int, new_status: str) -> Order | None:
        q = select(OrderModel).where(
            OrderModel.id == id_commande, OrderModel.deleted_at.is_(None)
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return None
        ligne.statut = new_status
        await self._session.flush()
        await self._session.refresh(ligne)
        return _order_to_entity(ligne)

    async def cancel(self, id_commande: int) -> Order | None:
        return await self.update_status(id_commande, "cancelled")
