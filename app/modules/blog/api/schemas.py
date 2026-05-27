"""Schemas Pydantic v2 du module blog."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BlogCategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class BlogPostSchema(BaseModel):
    """Schema de liste (sans content complet)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    excerpt: str | None
    author_name: str | None
    category_name: str | None
    thumbnail: str | None
    published_at: datetime | None
    views: int
    created_at: datetime
    updated_at: datetime


class BlogPostDetailSchema(BaseModel):
    """Schema de détail complet (avec content)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    excerpt: str | None
    content: str
    author_name: str | None
    category_name: str | None
    thumbnail: str | None
    published_at: datetime | None
    views: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class BlogPostCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    slug: str = Field(..., min_length=3, max_length=255, pattern=r"^[a-z0-9-]+$")
    excerpt: str | None = None
    content: str = Field(..., min_length=10)
    category_id: int | None = None
    thumbnail: str | None = Field(default=None, max_length=500)
    is_published: bool = False


class BlogPostUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    slug: str | None = Field(
        default=None, min_length=3, max_length=255, pattern=r"^[a-z0-9-]+$"
    )
    excerpt: str | None = None
    content: str | None = Field(default=None, min_length=10)
    category_id: int | None = None
    thumbnail: str | None = Field(default=None, max_length=500)
    is_published: bool | None = None
