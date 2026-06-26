"""Interfaces (ABC) des repositories du module product."""
from abc import ABC, abstractmethod
from decimal import Decimal

from app.modules.produit.domain.entites import (
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
    async def get_by_slug(self, identifiant_url: str) -> ProductCategory | None:
        ...

    @abstractmethod
    async def get_by_id(self, id_categorie: int) -> ProductCategory | None:
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def soft_delete(self, id_categorie: int) -> bool:
        ...


class BrandRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[Brand]:
        ...

    @abstractmethod
    async def get_by_id(self, id_marque: int) -> Brand | None:
        ...

    @abstractmethod
    async def create(
        self,
        nom: str,
        identifiant_url: str,
        logo: str | None,
        description: str | None,
        est_actif: bool,
    ) -> Brand:
        ...

    @abstractmethod
    async def update(
        self,
        id_marque: int,
        nom: str | None,
        identifiant_url: str | None,
        logo: str | None,
        description: str | None,
        est_actif: bool | None,
    ) -> Brand | None:
        ...

    @abstractmethod
    async def soft_delete(self, id_marque: int) -> bool:
        ...


class UnitRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id_unite: int) -> Unit | None:
        ...


class ProductRepository(ABC):
    @abstractmethod
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
        ...

    @abstractmethod
    async def get_by_slug(self, identifiant_url: str) -> Product | None:
        ...

    @abstractmethod
    async def get_by_id(self, id_produit: int) -> Product | None:
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def update(
        self,
        id_produit: int,
        **kwargs: object,
    ) -> Product | None:
        ...

    @abstractmethod
    async def soft_delete(self, id_produit: int) -> bool:
        ...

    @abstractmethod
    async def toggle_active(self, id_produit: int) -> Product | None:
        ...


class ProductImageRepository(ABC):
    @abstractmethod
    async def add_image(
        self,
        id_produit: int,
        image: str,
        est_principal: bool,
        ordre_affichage: int,
    ) -> ProductImage:
        ...

    @abstractmethod
    async def delete_image(self, image_id: int) -> bool:
        ...

    @abstractmethod
    async def list_for_product(self, id_produit: int) -> list[ProductImage]:
        ...


class ProductReviewRepository(ABC):
    @abstractmethod
    async def list_approved(
        self,
        id_produit: int,
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
    async def exists_for_user_product(self, id_utilisateur: int, id_produit: int) -> bool:
        ...

    @abstractmethod
    async def create(
        self,
        id_produit: int,
        id_utilisateur: int,
        note: int,
        commentaire: str | None,
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
    async def get_or_create(self, id_utilisateur: int) -> Cart:
        ...

    @abstractmethod
    async def get_by_user_id(self, id_utilisateur: int) -> Cart | None:
        ...

    @abstractmethod
    async def add_or_update_item(
        self,
        id_panier: int,
        id_produit: int,
        quantite: int,
        prix_unitaire: Decimal,
    ) -> CartItem:
        """Si id_produit existe déjà, additionne les quantités."""
        ...

    @abstractmethod
    async def update_item_quantity(
        self,
        id_panier: int,
        id_produit: int,
        quantite: int,
    ) -> CartItem | None:
        ...

    @abstractmethod
    async def remove_item(self, id_panier: int, id_produit: int) -> bool:
        ...

    @abstractmethod
    async def clear(self, id_panier: int) -> None:
        ...


class WishListRepository(ABC):
    @abstractmethod
    async def get_or_create(self, id_utilisateur: int) -> WishList:
        ...

    @abstractmethod
    async def add_item(self, id_liste_souhaits: int, id_produit: int) -> bool:
        """Retourne False si déjà présent."""
        ...

    @abstractmethod
    async def remove_item(self, id_liste_souhaits: int, id_produit: int) -> bool:
        ...


class OrderRepository(ABC):
    @abstractmethod
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
        ...

    @abstractmethod
    async def list_for_user(
        self,
        id_utilisateur: int,
        params: PaginationParams,
        statut: str | None = None,
    ) -> tuple[list[Order], int]:
        ...

    @abstractmethod
    async def list_all(
        self,
        params: PaginationParams,
        statut: str | None = None,
        id_utilisateur: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[list[Order], int]:
        ...

    @abstractmethod
    async def get_by_id(self, id_commande: int) -> Order | None:
        ...

    @abstractmethod
    async def update_status(self, id_commande: int, new_status: str) -> Order | None:
        ...

    @abstractmethod
    async def cancel(self, id_commande: int) -> Order | None:
        ...
