"""Schemas Pydantic v2 du module FAQ."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FAQSchema(BaseModel):
    """Schema de réponse pour une FAQ."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    answer: str
    category: str | None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class FAQCreateRequest(BaseModel):
    """Payload de création d'une FAQ (admin)."""

    question: str = Field(..., min_length=5, max_length=500)
    answer: str = Field(..., min_length=5)
    category: str | None = Field(default=None, max_length=100)
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0)


class FAQUpdateRequest(BaseModel):
    """Payload de mise à jour partielle d'une FAQ (admin)."""

    question: str | None = Field(default=None, min_length=5, max_length=500)
    answer: str | None = Field(default=None, min_length=5)
    category: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)
