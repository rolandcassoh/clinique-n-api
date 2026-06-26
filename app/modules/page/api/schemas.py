"""Schemas Pydantic v2 du module page (CMS)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PageSchema(BaseModel):
    """Schema de liste — sans contenu (allège la réponse)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    titre: str
    identifiant_url: str
    titre_meta: str | None
    meta_description: str | None
    est_publie: bool
    created_at: datetime
    updated_at: datetime


class PageDetailSchema(BaseModel):
    """Schema de détail — avec contenu complet."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    titre: str
    identifiant_url: str
    contenu: str
    titre_meta: str | None
    meta_description: str | None
    est_publie: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Requêtes
# ---------------------------------------------------------------------------


class PageCreateRequest(BaseModel):
    titre: str = Field(..., min_length=3, max_length=255)
    identifiant_url: str = Field(..., min_length=3, max_length=255, pattern=r"^[a-z0-9-]+$")
    contenu: str = Field(..., min_length=1)
    titre_meta: str | None = Field(default=None, max_length=255)
    meta_description: str | None = None
    est_publie: bool = True


class PageUpdateRequest(BaseModel):
    titre: str | None = Field(default=None, min_length=3, max_length=255)
    identifiant_url: str | None = Field(
        default=None, min_length=3, max_length=255, pattern=r"^[a-z0-9-]+$"
    )
    contenu: str | None = Field(default=None, min_length=1)
    titre_meta: str | None = Field(default=None, max_length=255)
    meta_description: str | None = None
    est_publie: bool | None = None
