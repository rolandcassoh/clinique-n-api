"""Schemas Pydantic v2 du module world."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    iso2: str
    iso3: str
    phone_code: str
    capital: str | None
    currency: str | None
    created_at: datetime
    updated_at: datetime


class StateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country_id: int
    name: str
    state_code: str
    created_at: datetime
    updated_at: datetime


class CitySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    state_id: int
    name: str
    created_at: datetime
    updated_at: datetime
