"""Schémas Pydantic v2 — module abonnements."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PlanLimitationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_plan: int
    fonctionnalite: str
    valeur: str
    created_at: datetime


class SubscriptionPlanSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    identifiant_url: str
    description: Optional[str]
    prix: Decimal
    periode_facturation: str
    jours_essai: int
    est_actif: bool
    est_mis_en_avant: bool
    ordre_affichage: int
    created_at: datetime
    limitations: list[PlanLimitationSchema] = []


class SubscriptionPlanCreateSchema(BaseModel):
    nom: str
    identifiant_url: str
    prix: float
    periode_facturation: str = "monthly"
    description: Optional[str] = None
    jours_essai: int = 0
    est_mis_en_avant: bool = False
    ordre_affichage: int = 0


class SubscriptionPlanUpdateSchema(BaseModel):
    nom: Optional[str] = None
    identifiant_url: Optional[str] = None
    prix: Optional[float] = None
    periode_facturation: Optional[str] = None
    description: Optional[str] = None
    jours_essai: Optional[int] = None
    est_actif: Optional[bool] = None
    est_mis_en_avant: Optional[bool] = None
    ordre_affichage: Optional[int] = None


class PlanLimitationUpsertSchema(BaseModel):
    fonctionnalite: str
    valeur: str


class SubscriptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_clinique: int
    id_plan: int
    statut: str
    debut_le: datetime
    fin_le: datetime
    renouvellement_auto: bool
    annule_le: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class SubscribeSchema(BaseModel):
    id_plan: int
    id_clinique: int


class RenewSchema(BaseModel):
    id_plan: Optional[int] = None


class ForceStatusSchema(BaseModel):
    statut: str
