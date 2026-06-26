"""Modèles SQLAlchemy du module product — tables compatibles Laravel."""
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import BaseModel
from app.database import Base


# ---------------------------------------------------------------------------
# Référentiels
# ---------------------------------------------------------------------------


class UnitModel(BaseModel):
    __tablename__ = "unites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    abréviation: Mapped[str] = mapped_column(String(20), nullable=False)

    products: Mapped[list["ProductModel"]] = relationship(
        "ProductModel", back_populates="unit", lazy="select"
    )


class ProductCategoryModel(BaseModel):
    __tablename__ = "categories_produits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    identifiant_url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    id_parent: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories_produits.id"), nullable=True)
    image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ordre_affichage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    children: Mapped[list["ProductCategoryModel"]] = relationship(
        "ProductCategoryModel",
        back_populates="parent",
        lazy="selectin",
        foreign_keys=[id_parent],
    )
    parent: Mapped["ProductCategoryModel | None"] = relationship(
        "ProductCategoryModel",
        back_populates="children",
        remote_side="ProductCategoryModel.id",
        foreign_keys=[id_parent],
    )
    products: Mapped[list["ProductModel"]] = relationship(
        "ProductModel", back_populates="category", lazy="select"
    )


class BrandModel(BaseModel):
    __tablename__ = "marques"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    identifiant_url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    products: Mapped[list["ProductModel"]] = relationship(
        "ProductModel", back_populates="brand", lazy="select"
    )


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


class ProductModel(BaseModel):
    __tablename__ = "produits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_prestataire: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id"), nullable=False)
    id_categorie: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories_produits.id"), nullable=False)
    id_marque: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("marques.id"), nullable=True)
    id_unite: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("unites.id"), nullable=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    identifiant_url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    prix: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    prix_remise: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    quantite_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reference_article: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    est_mis_en_avant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    poids: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    # id_taxe : pas de FK déclarée ici pour éviter une dépendance circulaire
    # avec le module taxes — la FK est définie dans la migration Alembic
    id_taxe: Mapped[int | None] = mapped_column(Integer, nullable=True)

    category: Mapped["ProductCategoryModel"] = relationship(
        "ProductCategoryModel", back_populates="products", lazy="selectin"
    )
    brand: Mapped["BrandModel | None"] = relationship(
        "BrandModel", back_populates="products", lazy="selectin"
    )
    unit: Mapped["UnitModel | None"] = relationship(
        "UnitModel", back_populates="products", lazy="selectin"
    )
    images: Mapped[list["ProductImageModel"]] = relationship(
        "ProductImageModel",
        back_populates="product",
        lazy="selectin",
        order_by="ProductImageModel.ordre_affichage",
    )
    reviews: Mapped[list["ProductReviewModel"]] = relationship(
        "ProductReviewModel", back_populates="product", lazy="select"
    )


class ProductImageModel(Base):
    """Pas de soft delete sur les images."""

    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_produit: Mapped[int] = mapped_column(
        Integer, ForeignKey("produits.id", ondelete="CASCADE"), nullable=False)
    image: Mapped[str] = mapped_column(String(500), nullable=False)
    est_principal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ordre_affichage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    from datetime import datetime
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    product: Mapped["ProductModel"] = relationship(
        "ProductModel", back_populates="images"
    )


class ProductReviewModel(BaseModel):
    __tablename__ = "product_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_produit: Mapped[int] = mapped_column(
        Integer, ForeignKey("produits.id"), nullable=False)
    id_utilisateur: Mapped[int] = mapped_column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    note: Mapped[int] = mapped_column(Integer, nullable=False)
    commentaire: Mapped[str | None] = mapped_column(Text, nullable=True)
    est_approuve: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    product: Mapped["ProductModel"] = relationship(
        "ProductModel", back_populates="reviews"
    )


# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------


class CartModel(Base):
    __tablename__ = "paniers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id"), unique=True, nullable=False)

    from datetime import datetime
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    items: Mapped[list["CartItemModel"]] = relationship(
        "CartItemModel",
        back_populates="cart",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class CartItemModel(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_panier: Mapped[int] = mapped_column(
        Integer, ForeignKey("paniers.id", ondelete="CASCADE"), nullable=False)
    id_produit: Mapped[int] = mapped_column(
        Integer, ForeignKey("produits.id"), nullable=False)
    quantite: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    prix_unitaire: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    from datetime import datetime
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("id_panier", "id_produit", name="uq_cart_items_cart_product"),
    )

    cart: Mapped["CartModel"] = relationship("CartModel", back_populates="items")
    product: Mapped["ProductModel"] = relationship("ProductModel", lazy="selectin")


# ---------------------------------------------------------------------------
# WishList
# ---------------------------------------------------------------------------


class WishListModel(Base):
    __tablename__ = "listes_souhaits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id"), unique=True, nullable=False)

    from datetime import datetime
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    items: Mapped[list["WishListItemModel"]] = relationship(
        "WishListItemModel",
        back_populates="wish_list",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class WishListItemModel(Base):
    __tablename__ = "wish_list_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_liste_souhaits: Mapped[int] = mapped_column(
        Integer, ForeignKey("listes_souhaits.id", ondelete="CASCADE"), nullable=False)
    id_produit: Mapped[int] = mapped_column(
        Integer, ForeignKey("produits.id"), nullable=False)

    from datetime import datetime
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "id_liste_souhaits", "id_produit", name="uq_wishlist_items_list_product"
        ),
    )

    wish_list: Mapped["WishListModel"] = relationship("WishListModel", back_populates="items")
    product: Mapped["ProductModel"] = relationship("ProductModel", lazy="selectin")


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


class OrderModel(BaseModel):
    __tablename__ = "commandes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reference: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    id_utilisateur: Mapped[int] = mapped_column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    id_prestataire: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("utilisateurs.id"), nullable=True)
    sous_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    montant_remise: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False)
    montant_taxe: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False)
    frais_livraison: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    statut: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "processing",
            "shipped",
            "delivered",
            "cancelled",
            "refunded",
            name="order_status_enum",
            native_enum=False,
        ),
        default="pending",
        nullable=False)
    statut_paiement: Mapped[str] = mapped_column(
        Enum("pending", "paid", "refunded", name="order_payment_status_enum", native_enum=False),
        default="pending",
        nullable=False)
    passerelle_paiement: Mapped[str | None] = mapped_column(String(50), nullable=True)
    adresse_livraison: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # id_promotion : pas de FK déclarée ici — dépendance externe gérée via migration Alembic
    id_promotion: Mapped[int | None] = mapped_column(Integer, nullable=True)

    items: Mapped[list["OrderItemModel"]] = relationship(
        "OrderItemModel",
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class OrderItemModel(Base):
    __tablename__ = "articles_commande"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_commande: Mapped[int] = mapped_column(
        Integer, ForeignKey("commandes.id", ondelete="CASCADE"), nullable=False)
    id_produit: Mapped[int] = mapped_column(Integer, ForeignKey("produits.id"), nullable=False)
    nom_produit: Mapped[str] = mapped_column(String(255), nullable=False)
    prix_unitaire: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantite: Mapped[int] = mapped_column(Integer, nullable=False)
    sous_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    from datetime import datetime
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    order: Mapped["OrderModel"] = relationship("OrderModel", back_populates="items")
    product: Mapped["ProductModel"] = relationship("ProductModel", lazy="selectin")
