"""Schemas Pydantic v2 du module FAQ."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FAQSchema(BaseModel):
    """Schema de réponse pour une FAQ."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    reponse: str
    category: str | None
    est_actif: bool
    ordre_affichage: int
    created_at: datetime
    updated_at: datetime


class FAQCreateRequest(BaseModel):
    """Payload de création d'une FAQ (admin)."""

    question: str = Field(..., min_length=5, max_length=500)
    reponse: str = Field(..., min_length=5)
    category: str | None = Field(default=None, max_length=100)
    est_actif: bool = True
    ordre_affichage: int = Field(default=0, ge=0)


class FAQUpdateRequest(BaseModel):
    """Payload de mise à jour partielle d'une FAQ (admin)."""

    question: str | None = Field(default=None, min_length=5, max_length=500)
    reponse: str | None = Field(default=None, min_length=5)
    category: str | None = Field(default=None, max_length=100)
    est_actif: bool | None = None
    ordre_affichage: int | None = Field(default=None, ge=0)
