from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PromotionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    nom: str
    type: str
    valeur: Decimal
    montant_min_commande: Decimal | None
    remise_maximale: Decimal | None
    limite_utilisation: int | None
    compteur_utilisation: int
    debut_le: datetime | None
    expire_le: datetime | None
    est_actif: bool
    applicable_a: str
    created_at: datetime


class PromotionCreateSchema(BaseModel):
    code: str = Field(max_length=50)
    nom: str = Field(max_length=255)
    type: str  # 'percentage' | 'fixed'
    valeur: Decimal = Field(gt=0)
    montant_min_commande: Decimal | None = None
    remise_maximale: Decimal | None = None
    limite_utilisation: int | None = None
    debut_le: datetime | None = None
    expire_le: datetime | None = None
    est_actif: bool = True
    applicable_a: str = "all"


class PromotionUpdateSchema(BaseModel):
    code: str = Field(max_length=50)
    nom: str = Field(max_length=255)
    type: str
    valeur: Decimal = Field(gt=0)
    montant_min_commande: Decimal | None = None
    remise_maximale: Decimal | None = None
    limite_utilisation: int | None = None
    debut_le: datetime | None = None
    expire_le: datetime | None = None
    est_actif: bool = True
    applicable_a: str = "all"


class ValidatePromotionRequestSchema(BaseModel):
    code: str
    montant: Decimal = Field(gt=0)
    applicable_a: str = "all"


class ValidatePromotionResponseSchema(BaseModel):
    valid: bool
    montant_remise: float
    promotion: PromotionSchema | None
    motif: str | None = None


class PromotionUseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_promotion: int
    id_utilisateur: int
    id_commande: int | None
    id_rendez_vous: int | None
    montant_remise: Decimal
    utilise_le: datetime
    created_at: datetime
