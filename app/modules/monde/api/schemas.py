"""Schemas Pydantic v2 du module world."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    code_iso2: str
    code_iso3: str
    indicatif_telephone: str
    capitale: str | None
    devise: str | None
    created_at: datetime
    updated_at: datetime


class StateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_pays: int
    nom: str
    code_region: str
    created_at: datetime
    updated_at: datetime


class CitySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_region: int
    nom: str
    created_at: datetime
    updated_at: datetime
