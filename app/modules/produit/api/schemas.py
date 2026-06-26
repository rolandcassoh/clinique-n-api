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
    nom: str
    identifiant_url: str
    id_parent: int | None
    image: str | None
    description: str | None
    est_actif: bool
    ordre_affichage: int
    children: list["ProductCategorySchema"] = []
    created_at: datetime
    updated_at: datetime


ProductCategorySchema.model_rebuild()


class ProductCategoryCreateRequest(BaseModel):
    nom: str = Field(..., min_length=2, max_length=255)
    identifiant_url: str = Field(..., min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$")
    id_parent: int | None = None
    image: str | None = Field(default=None, max_length=500)
    description: str | None = None
    est_actif: bool = True
    ordre_affichage: int = 0


class ProductCategoryUpdateRequest(BaseModel):
    nom: str | None = Field(default=None, min_length=2, max_length=255)
    identifiant_url: str | None = Field(
        default=None, min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$"
    )
    id_parent: int | None = None
    image: str | None = None
    description: str | None = None
    est_actif: bool | None = None
    ordre_affichage: int | None = None


# ---------------------------------------------------------------------------
# Marques
# ---------------------------------------------------------------------------


class BrandSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    identifiant_url: str
    logo: str | None
    description: str | None
    est_actif: bool
    created_at: datetime
    updated_at: datetime


class BrandCreateRequest(BaseModel):
    nom: str = Field(..., min_length=2, max_length=255)
    identifiant_url: str = Field(..., min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$")
    logo: str | None = Field(default=None, max_length=500)
    description: str | None = None
    est_actif: bool = True


class BrandUpdateRequest(BaseModel):
    nom: str | None = Field(default=None, min_length=2, max_length=255)
    identifiant_url: str | None = Field(
        default=None, min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$"
    )
    logo: str | None = None
    description: str | None = None
    est_actif: bool | None = None


# ---------------------------------------------------------------------------
# Images produits
# ---------------------------------------------------------------------------


class ProductImageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_produit: int
    image: str
    est_principal: bool
    ordre_affichage: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Produits
# ---------------------------------------------------------------------------


class ProductListSchema(BaseModel):
    """Schema allégé pour la liste."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    identifiant_url: str
    short_description: str | None
    prix: Decimal
    prix_remise: Decimal | None
    quantite_stock: int
    est_actif: bool
    est_mis_en_avant: bool
    category_name: str | None
    brand_name: str | None
    images: list[ProductImageSchema] = []
    created_at: datetime
    updated_at: datetime


class ProductDetailSchema(BaseModel):
    """Schema complet avec images et review_summary."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    id_prestataire: int
    id_categorie: int
    id_marque: int | None
    id_unite: int | None
    nom: str
    identifiant_url: str
    description: str | None
    short_description: str | None
    prix: Decimal
    prix_remise: Decimal | None
    quantite_stock: int
    reference_article: str | None
    est_actif: bool
    est_mis_en_avant: bool
    poids: Decimal | None
    id_taxe: int | None
    category_name: str | None
    brand_name: str | None
    unit_name: str | None
    images: list[ProductImageSchema] = []
    created_at: datetime
    updated_at: datetime


class ProductCreateRequest(BaseModel):
    id_prestataire: int
    id_categorie: int
    id_marque: int | None = None
    id_unite: int | None = None
    nom: str = Field(..., min_length=2, max_length=255)
    identifiant_url: str = Field(..., min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    short_description: str | None = Field(default=None, max_length=500)
    prix: Decimal = Field(..., gt=0)
    prix_remise: Decimal | None = Field(default=None, gt=0)
    quantite_stock: int = Field(default=0, ge=0)
    reference_article: str | None = Field(default=None, max_length=100)
    est_actif: bool = True
    est_mis_en_avant: bool = False
    poids: Decimal | None = None
    id_taxe: int | None = None


class ProductUpdateRequest(BaseModel):
    id_categorie: int | None = None
    id_marque: int | None = None
    id_unite: int | None = None
    nom: str | None = Field(default=None, min_length=2, max_length=255)
    identifiant_url: str | None = Field(
        default=None, min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$"
    )
    description: str | None = None
    short_description: str | None = None
    prix: Decimal | None = Field(default=None, gt=0)
    prix_remise: Decimal | None = None
    quantite_stock: int | None = Field(default=None, ge=0)
    reference_article: str | None = None
    est_actif: bool | None = None
    est_mis_en_avant: bool | None = None
    poids: Decimal | None = None
    id_taxe: int | None = None


# ---------------------------------------------------------------------------
# Avis produits
# ---------------------------------------------------------------------------


class ProductReviewSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_produit: int
    id_utilisateur: int
    note: int
    commentaire: str | None
    est_approuve: bool
    created_at: datetime
    updated_at: datetime


class ProductReviewCreateRequest(BaseModel):
    note: int = Field(..., ge=1, le=5)
    commentaire: str | None = None


# ---------------------------------------------------------------------------
# Panier
# ---------------------------------------------------------------------------


class CartItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_panier: int
    id_produit: int
    quantite: int
    prix_unitaire: Decimal
    sous_total: Decimal
    nom_produit: str | None
    product_image: str | None
    created_at: datetime
    updated_at: datetime


class CartSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_utilisateur: int
    items: list[CartItemSchema] = []
    total: Decimal
    item_count: int
    created_at: datetime
    updated_at: datetime


class AddToCartRequest(BaseModel):
    id_produit: int
    quantite: int = Field(..., ge=1)


class UpdateCartItemRequest(BaseModel):
    quantite: int = Field(..., ge=1)


# ---------------------------------------------------------------------------
# Liste de souhaits
# ---------------------------------------------------------------------------


class WishListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_liste_souhaits: int
    id_produit: int
    nom_produit: str | None
    product_image: str | None
    product_price: Decimal | None
    created_at: datetime
    updated_at: datetime


class WishListSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_utilisateur: int
    items: list[WishListItemSchema] = []
    created_at: datetime
    updated_at: datetime


class AddToWishListRequest(BaseModel):
    id_produit: int


# ---------------------------------------------------------------------------
# Commandes
# ---------------------------------------------------------------------------


class OrderItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_commande: int
    id_produit: int
    nom_produit: str
    prix_unitaire: Decimal
    quantite: int
    sous_total: Decimal
    created_at: datetime
    updated_at: datetime


class OrderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference: str
    id_utilisateur: int
    id_prestataire: int | None
    sous_total: Decimal
    montant_remise: Decimal
    montant_taxe: Decimal
    frais_livraison: Decimal
    total: Decimal
    statut: str
    statut_paiement: str
    passerelle_paiement: str | None
    adresse_livraison: str | None
    notes: str | None
    id_promotion: int | None
    items: list[OrderItemSchema] = []
    created_at: datetime
    updated_at: datetime


class CreateOrderRequest(BaseModel):
    passerelle_paiement: str | None = Field(default=None, max_length=50)
    adresse_livraison: str | None = None
    promotion_code: str | None = None
    notes: str | None = None


class UpdateOrderStatusRequest(BaseModel):
    statut: str = Field(..., pattern=r"^(processing|shipped|delivered)$")
