"""Schemas Pydantic v2 du module blog."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BlogCategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    identifiant_url: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class BlogPostSchema(BaseModel):
    """Schema de liste (sans contenu complet)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    titre: str
    identifiant_url: str
    extrait: str | None
    author_name: str | None
    category_name: str | None
    miniature: str | None
    est_publie: bool
    publie_le: datetime | None
    vues: int
    created_at: datetime
    updated_at: datetime


class BlogPostDetailSchema(BaseModel):
    """Schema de détail complet (avec contenu)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    titre: str
    identifiant_url: str
    extrait: str | None
    contenu: str
    author_name: str | None
    category_name: str | None
    miniature: str | None
    est_publie: bool
    publie_le: datetime | None
    vues: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class BlogPostCreateRequest(BaseModel):
    titre: str = Field(..., min_length=3, max_length=255)
    identifiant_url: str = Field(..., min_length=3, max_length=255, pattern=r"^[a-z0-9-]+$")
    extrait: str | None = None
    contenu: str = Field(..., min_length=10)
    id_categorie: int | None = None
    miniature: str | None = Field(default=None, max_length=500)
    est_publie: bool = False


class BlogPostUpdateRequest(BaseModel):
    titre: str | None = Field(default=None, min_length=3, max_length=255)
    identifiant_url: str | None = Field(
        default=None, min_length=3, max_length=255, pattern=r"^[a-z0-9-]+$"
    )
    extrait: str | None = None
    contenu: str | None = Field(default=None, min_length=10)
    id_categorie: int | None = None
    miniature: str | None = Field(default=None, max_length=500)
    est_publie: bool | None = None
