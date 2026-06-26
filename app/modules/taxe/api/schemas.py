from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TaxSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    tarif: Decimal
    type: str
    id_pays: int | None
    est_defaut: bool
    est_actif: bool
    created_at: datetime


class TaxCreateSchema(BaseModel):
    nom: str = Field(max_length=100)
    tarif: Decimal = Field(ge=0)
    type: str = "percentage"
    id_pays: int | None = None
    est_defaut: bool = False
    est_actif: bool = True


class TaxUpdateSchema(BaseModel):
    nom: str = Field(max_length=100)
    tarif: Decimal = Field(ge=0)
    type: str = "percentage"
    id_pays: int | None = None
    est_defaut: bool = False
    est_actif: bool = True
