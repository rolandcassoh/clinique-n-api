"""Schemas Pydantic v2 du module Logistic."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ShippingZoneSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    description: str | None
    est_actif: bool
    created_at: datetime
    updated_at: datetime


class ShippingZoneCreateRequest(BaseModel):
    nom: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    est_actif: bool = True


class ShippingZoneUpdateRequest(BaseModel):
    nom: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    est_actif: bool | None = None


class ShippingRateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_zone: int
    nom: str
    poids_min: Decimal
    poids_max: Decimal | None
    montant_min_commande: Decimal
    tarif: Decimal
    livraison_gratuite: bool
    jours_livraison_min: int
    jours_livraison_max: int
    est_actif: bool
    created_at: datetime
    updated_at: datetime


class ShippingRateCreateRequest(BaseModel):
    id_zone: int
    nom: str = Field(..., min_length=1, max_length=255)
    tarif: Decimal = Field(..., ge=0)
    poids_min: Decimal = Field(default=Decimal("0"), ge=0)
    poids_max: Decimal | None = Field(default=None, ge=0)
    montant_min_commande: Decimal = Field(default=Decimal("0"), ge=0)
    livraison_gratuite: bool = False
    jours_livraison_min: int = Field(default=1, ge=1)
    jours_livraison_max: int = Field(default=3, ge=1)
    est_actif: bool = True


class ShippingRateUpdateRequest(BaseModel):
    nom: str | None = Field(default=None, min_length=1, max_length=255)
    tarif: Decimal | None = Field(default=None, ge=0)
    poids_min: Decimal | None = Field(default=None, ge=0)
    poids_max: Decimal | None = Field(default=None, ge=0)
    montant_min_commande: Decimal | None = Field(default=None, ge=0)
    livraison_gratuite: bool | None = None
    jours_livraison_min: int | None = Field(default=None, ge=1)
    jours_livraison_max: int | None = Field(default=None, ge=1)
    est_actif: bool | None = None


class ShippingCalculationSchema(BaseModel):
    """Résultat du calcul de frais de livraison."""
    tarif: Decimal
    jours_livraison_min: int
    jours_livraison_max: int
    rate_name: str
    livraison_gratuite: bool
