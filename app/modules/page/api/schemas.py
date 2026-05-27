"""Schemas Pydantic v2 du module page (CMS)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PageSchema(BaseModel):
    """Schema de liste — sans content (allège la réponse)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    meta_title: str | None
    meta_description: str | None
    is_published: bool
    created_at: datetime
    updated_at: datetime


class PageDetailSchema(BaseModel):
    """Schema de détail — avec content complet."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    content: str
    meta_title: str | None
    meta_description: str | None
    is_published: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class PageCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    slug: str = Field(..., min_length=3, max_length=255, pattern=r"^[a-z0-9-]+$")
    content: str = Field(..., min_length=1)
    meta_title: str | None = Field(default=None, max_length=255)
    meta_description: str | None = None
    is_published: bool = True


class PageUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    slug: str | None = Field(
        default=None, min_length=3, max_length=255, pattern=r"^[a-z0-9-]+$"
    )
    content: str | None = Field(default=None, min_length=1)
    meta_title: str | None = Field(default=None, max_length=255)
    meta_description: str | None = None
    is_published: bool | None = None
