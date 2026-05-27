"""Schemas Pydantic v2 du module Service."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Category Schemas
# ---------------------------------------------------------------------------

class ServiceCategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    image: str | None
    description: str | None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ServiceCategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    image: str | None = Field(default=None, max_length=500)
    description: str | None = None
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0)


class ServiceCategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    image: str | None = Field(default=None, max_length=500)
    description: str | None = None
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)


# ---------------------------------------------------------------------------
# Gallery Schemas
# ---------------------------------------------------------------------------

class ServiceGallerySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    image: str
    caption: str | None
    sort_order: int


class ServiceGalleryCreateRequest(BaseModel):
    image: str = Field(..., max_length=500)
    caption: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0, ge=0)


class GalleryReorderItem(BaseModel):
    id: int
    sort_order: int = Field(ge=0)


class GalleryReorderRequest(BaseModel):
    items: list[GalleryReorderItem]


# ---------------------------------------------------------------------------
# Package Schemas
# ---------------------------------------------------------------------------

class ServicePackageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    name: str
    description: str | None
    price: Decimal
    sessions_count: int
    validity_days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ServicePackageCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(..., gt=0)
    sessions_count: int = Field(default=1, ge=1)
    validity_days: int = Field(default=30, ge=1)
    is_active: bool = True


class ServicePackageUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0)
    sessions_count: int | None = Field(default=None, ge=1)
    validity_days: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# Employee Schemas
# ---------------------------------------------------------------------------

class ServiceEmployeeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    user_id: int
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class ServiceEmployeeAssignRequest(BaseModel):
    user_id: int
    is_primary: bool = False


# ---------------------------------------------------------------------------
# Review Schemas
# ---------------------------------------------------------------------------

class ServiceReviewSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    user_id: int
    rating: int
    comment: str | None
    is_approved: bool
    created_at: datetime
    updated_at: datetime


class ServiceReviewCreateRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


# ---------------------------------------------------------------------------
# Service Schemas
# ---------------------------------------------------------------------------

class ServiceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vendor_id: int
    category_id: int | None
    name: str
    slug: str
    description: str | None
    short_description: str | None
    price: Decimal
    discount_price: Decimal | None
    effective_price: Decimal
    is_discounted: bool
    duration_minutes: int
    is_active: bool
    is_featured: bool
    is_home_service: bool
    max_members: int
    average_rating: float | None
    review_count: int
    rating_display: str
    category: ServiceCategorySchema | None = None
    galleries: list[ServiceGallerySchema] = []
    packages: list[ServicePackageSchema] = []
    employees: list[ServiceEmployeeSchema] = []
    created_at: datetime
    updated_at: datetime


class ServiceCreateRequest(BaseModel):
    vendor_id: int
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    price: Decimal = Field(..., gt=0)
    category_id: int | None = None
    description: str | None = None
    short_description: str | None = Field(default=None, max_length=500)
    discount_price: Decimal | None = Field(default=None, gt=0)
    duration_minutes: int = Field(default=60, ge=1)
    is_active: bool = True
    is_featured: bool = False
    is_home_service: bool = False
    max_members: int = Field(default=1, ge=1)


class ServiceUpdateRequest(BaseModel):
    vendor_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    price: Decimal | None = Field(default=None, gt=0)
    category_id: int | None = None
    description: str | None = None
    short_description: str | None = Field(default=None, max_length=500)
    discount_price: Decimal | None = Field(default=None, gt=0)
    duration_minutes: int | None = Field(default=None, ge=1)
    is_active: bool | None = None
    is_featured: bool | None = None
    is_home_service: bool | None = None
    max_members: int | None = Field(default=None, ge=1)
