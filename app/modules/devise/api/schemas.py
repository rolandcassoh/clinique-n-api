"""Schemas Pydantic v2 du module devise (devise)."""
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class CurrencySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    code: str
    symbole: str
    taux_change: Decimal
    est_defaut: bool


class CurrencyCreateSchema(BaseModel):
    nom: str
    code: str
    symbole: str
    taux_change: Decimal = Decimal("1")
    est_defaut: bool = False
    est_actif: bool = True

    @field_validator("code")
    @classmethod
    def code_uppercase(cls, v: str) -> str:
        return v.upper()


class CurrencyUpdateSchema(BaseModel):
    nom: str
    code: str
    symbole: str
    taux_change: Decimal
    est_defaut: bool = False
    est_actif: bool = True

    @field_validator("code")
    @classmethod
    def code_uppercase(cls, v: str) -> str:
        return v.upper()
