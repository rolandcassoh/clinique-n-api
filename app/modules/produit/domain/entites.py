"""Entités domaine product — aucune dépendance externe (pas de FastAPI/SQLAlchemy)."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


# ---------------------------------------------------------------------------
# Value Object — Money
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Money:
    montant: Decimal
    devise: str = "XAF"

    def __post_init__(self) -> None:
        if self.montant < 0:
            raise ValueError("Le montant ne peut pas être négatif")

    def apply_percentage_discount(self, tarif: Decimal) -> "Money":
        return Money(self.montant * (1 - tarif / 100), self.devise)

    def __add__(self, other: "Money") -> "Money":
        if self.devise != other.devise:
            raise ValueError("Impossible d'additionner des montants de devises différentes")
        return Money(self.montant + other.montant, self.devise)

    def __mul__(self, factor: Decimal | int) -> "Money":
        return Money(self.montant * Decimal(str(factor)), self.devise)


# ---------------------------------------------------------------------------
# Domain entities
# ---------------------------------------------------------------------------


@dataclass
class ProductCategory:
    id: int
    nom: str
    identifiant_url: str
    id_parent: int | None
    image: str | None
    description: str | None
    est_actif: bool
    ordre_affichage: int
    children: list["ProductCategory"] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"ProductCategory({self.identifiant_url}: {self.nom})"


@dataclass
class Brand:
    id: int
    nom: str
    identifiant_url: str
    logo: str | None
    description: str | None
    est_actif: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"Brand({self.identifiant_url}: {self.nom})"


@dataclass
class Unit:
    id: int
    nom: str
    abréviation: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProductImage:
    id: int
    id_produit: int
    image: str
    est_principal: bool
    ordre_affichage: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProductReviewSummary:
    count: int
    average: Decimal


@dataclass
class Product:
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
    # Relations dénormalisées pour la réponse
    category_name: str | None = None
    brand_name: str | None = None
    unit_name: str | None = None
    images: list[ProductImage] = field(default_factory=list)
    review_summary: ProductReviewSummary | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def effective_price(self) -> Decimal:
        """Retourne le prix effectif (réduit si applicable)."""
        if self.prix_remise is not None and self.prix_remise < self.prix:
            return self.prix_remise
        return self.prix

    @property
    def is_in_stock(self) -> bool:
        return self.quantite_stock > 0

    def has_enough_stock(self, quantite: int) -> bool:
        return self.quantite_stock >= quantite

    def __str__(self) -> str:
        return f"Product({self.identifiant_url}: {self.nom})"


@dataclass
class ProductReview:
    id: int
    id_produit: int
    id_utilisateur: int
    note: int
    commentaire: str | None
    est_approuve: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not 1 <= self.note <= 5:
            raise ValueError("La note doit être comprise entre 1 et 5")


# ---------------------------------------------------------------------------
# Cart entities
# ---------------------------------------------------------------------------


@dataclass
class CartItem:
    id: int
    id_panier: int
    id_produit: int
    quantite: int
    prix_unitaire: Decimal
    # Dénormalisé pour la réponse
    nom_produit: str | None = None
    product_image: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def sous_total(self) -> Decimal:
        return self.prix_unitaire * self.quantite


@dataclass
class Cart:
    id: int
    id_utilisateur: int
    items: list[CartItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def total(self) -> Decimal:
        return sum((item.sous_total for item in self.items), Decimal("0"))

    @property
    def item_count(self) -> int:
        return len(self.items)

    def find_item(self, id_produit: int) -> CartItem | None:
        for item in self.items:
            if item.id_produit == id_produit:
                return item
        return None

    def is_empty(self) -> bool:
        return len(self.items) == 0


# ---------------------------------------------------------------------------
# Wishlist entities
# ---------------------------------------------------------------------------


@dataclass
class WishListItem:
    id: int
    id_liste_souhaits: int
    id_produit: int
    nom_produit: str | None = None
    product_image: str | None = None
    product_price: Decimal | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class WishList:
    id: int
    id_utilisateur: int
    items: list[WishListItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Order entities
# ---------------------------------------------------------------------------


@dataclass
class OrderItem:
    id: int
    id_commande: int
    id_produit: int
    nom_produit: str
    prix_unitaire: Decimal
    quantite: int
    sous_total: Decimal
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Order:
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
    items: list[OrderItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    CANCELLABLE_STATUSES = ("pending", "processing")

    def can_cancel(self) -> bool:
        return self.statut in self.CANCELLABLE_STATUSES

    def __str__(self) -> str:
        return f"Order({self.reference}: {self.statut})"
