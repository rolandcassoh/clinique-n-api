"""Modèles SQLAlchemy du module Service — tables compatibles Laravel."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DECIMAL,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import BaseModel


class ServiceCategoryModel(BaseModel):
    __tablename__ = "categories_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    identifiant_url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ordre_affichage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    services: Mapped[list[ServiceModel]] = relationship(back_populates="category")


class ServiceModel(BaseModel):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_prestataire: Mapped[int] = mapped_column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    id_categorie: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories_services.id"), nullable=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    identifiant_url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    prix: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    prix_remise: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True)
    duree_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    est_mis_en_avant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    service_domicile: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_membres: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    category: Mapped[ServiceCategoryModel | None] = relationship(back_populates="services")
    packages: Mapped[list[ServicePackageModel]] = relationship(back_populates="service")
    employees: Mapped[list[ServiceEmployeeModel]] = relationship(back_populates="service")
    galleries: Mapped[list[ServiceGalleryModel]] = relationship(
        back_populates="service", order_by="ServiceGalleryModel.ordre_affichage"
    )
    reviews: Mapped[list[ServiceReviewModel]] = relationship(back_populates="service")


class ServicePackageModel(BaseModel):
    __tablename__ = "forfaits_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_service: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    prix: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    nombre_seances: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    jours_validite: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    service: Mapped[ServiceModel] = relationship(back_populates="packages")


class ServiceEmployeeModel(BaseModel):
    __tablename__ = "service_employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_service: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    id_utilisateur: Mapped[int] = mapped_column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    est_principal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    service: Mapped[ServiceModel] = relationship(back_populates="employees")


class ServiceGalleryModel(BaseModel):
    __tablename__ = "service_galleries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_service: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    image: Mapped[str] = mapped_column(String(500), nullable=False)
    legende: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ordre_affichage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    service: Mapped[ServiceModel] = relationship(back_populates="galleries")


class ServiceReviewModel(BaseModel):
    __tablename__ = "service_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_service: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    id_utilisateur: Mapped[int] = mapped_column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    note: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    commentaire: Mapped[str | None] = mapped_column(Text, nullable=True)
    est_approuve: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    service: Mapped[ServiceModel] = relationship(back_populates="reviews")
