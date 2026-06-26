"""Schemas Pydantic v2 du module Service."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Category Schemas
# ---------------------------------------------------------------------------

class ServiceCategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    identifiant_url: str
    image: str | None
    description: str | None
    est_actif: bool
    ordre_affichage: int
    created_at: datetime
    updated_at: datetime


class ServiceCategoryCreateRequest(BaseModel):
    nom: str = Field(..., min_length=1, max_length=255)
    identifiant_url: str = Field(..., min_length=1, max_length=255)
    image: str | None = Field(default=None, max_length=500)
    description: str | None = None
    est_actif: bool = True
    ordre_affichage: int = Field(default=0, ge=0)


class ServiceCategoryUpdateRequest(BaseModel):
    nom: str | None = Field(default=None, min_length=1, max_length=255)
    identifiant_url: str | None = Field(default=None, min_length=1, max_length=255)
    image: str | None = Field(default=None, max_length=500)
    description: str | None = None
    est_actif: bool | None = None
    ordre_affichage: int | None = Field(default=None, ge=0)


# ---------------------------------------------------------------------------
# Gallery Schemas
# ---------------------------------------------------------------------------

class ServiceGallerySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_service: int
    image: str
    legende: str | None
    ordre_affichage: int


class ServiceGalleryCreateRequest(BaseModel):
    image: str = Field(..., max_length=500)
    legende: str | None = Field(default=None, max_length=255)
    ordre_affichage: int = Field(default=0, ge=0)


class GalleryReorderItem(BaseModel):
    id: int
    ordre_affichage: int = Field(ge=0)


class GalleryReorderRequest(BaseModel):
    items: list[GalleryReorderItem]


# ---------------------------------------------------------------------------
# Package Schemas
# ---------------------------------------------------------------------------

class ServicePackageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_service: int
    nom: str
    description: str | None
    prix: Decimal
    nombre_seances: int
    jours_validite: int
    est_actif: bool
    created_at: datetime
    updated_at: datetime


class ServicePackageCreateRequest(BaseModel):
    nom: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    prix: Decimal = Field(..., gt=0)
    nombre_seances: int = Field(default=1, ge=1)
    jours_validite: int = Field(default=30, ge=1)
    est_actif: bool = True


class ServicePackageUpdateRequest(BaseModel):
    nom: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    prix: Decimal | None = Field(default=None, gt=0)
    nombre_seances: int | None = Field(default=None, ge=1)
    jours_validite: int | None = Field(default=None, ge=1)
    est_actif: bool | None = None


# ---------------------------------------------------------------------------
# Employee Schemas
# ---------------------------------------------------------------------------

class ServiceEmployeeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_service: int
    id_utilisateur: int
    est_principal: bool
    created_at: datetime
    updated_at: datetime


class ServiceEmployeeAssignRequest(BaseModel):
    id_utilisateur: int
    est_principal: bool = False


# ---------------------------------------------------------------------------
# Review Schemas
# ---------------------------------------------------------------------------

class ServiceReviewSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_service: int
    id_utilisateur: int
    note: int
    commentaire: str | None
    est_approuve: bool
    created_at: datetime
    updated_at: datetime


class ServiceReviewCreateRequest(BaseModel):
    note: int = Field(..., ge=1, le=5)
    commentaire: str | None = None


# ---------------------------------------------------------------------------
# Service Schemas
# ---------------------------------------------------------------------------

class ServiceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_prestataire: int
    id_categorie: int | None
    nom: str
    identifiant_url: str
    description: str | None
    short_description: str | None
    prix: Decimal
    prix_remise: Decimal | None
    effective_price: Decimal
    is_discounted: bool
    duree_minutes: int
    est_actif: bool
    est_mis_en_avant: bool
    service_domicile: bool
    max_membres: int
    note_moyenne: float | None
    review_count: int
    rating_display: str
    category: ServiceCategorySchema | None = None
    galleries: list[ServiceGallerySchema] = []
    packages: list[ServicePackageSchema] = []
    employees: list[ServiceEmployeeSchema] = []
    created_at: datetime
    updated_at: datetime


class ServiceCreateRequest(BaseModel):
    id_prestataire: int
    nom: str = Field(..., min_length=1, max_length=255)
    identifiant_url: str = Field(..., min_length=1, max_length=255)
    prix: Decimal = Field(..., gt=0)
    id_categorie: int | None = None
    description: str | None = None
    short_description: str | None = Field(default=None, max_length=500)
    prix_remise: Decimal | None = Field(default=None, gt=0)
    duree_minutes: int = Field(default=60, ge=1)
    est_actif: bool = True
    est_mis_en_avant: bool = False
    service_domicile: bool = False
    max_membres: int = Field(default=1, ge=1)


class ServiceUpdateRequest(BaseModel):
    id_prestataire: int | None = None
    nom: str | None = Field(default=None, min_length=1, max_length=255)
    identifiant_url: str | None = Field(default=None, min_length=1, max_length=255)
    prix: Decimal | None = Field(default=None, gt=0)
    id_categorie: int | None = None
    description: str | None = None
    short_description: str | None = Field(default=None, max_length=500)
    prix_remise: Decimal | None = Field(default=None, gt=0)
    duree_minutes: int | None = Field(default=None, ge=1)
    est_actif: bool | None = None
    est_mis_en_avant: bool | None = None
    service_domicile: bool | None = None
    max_membres: int | None = Field(default=None, ge=1)
