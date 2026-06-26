"""Schemas Pydantic v2 du module tag."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TagSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    identifiant_url: str
    type: str | None
    created_at: datetime


class TagCreateSchema(BaseModel):
    nom: str
    identifiant_url: str
    type: str | None = None


class TagUpdateSchema(BaseModel):
    nom: str
    identifiant_url: str
    type: str | None = None
