"""Schemas Pydantic v2 du module RequestService."""
from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.request_service.domain.entities import RequestServiceStatus


class RequestServiceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    category_id: int | None
    title: str
    description: str
    location: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    budget_min: Decimal | None
    budget_max: Decimal | None
    preferred_date: date | None
    preferred_time: time | None
    status: RequestServiceStatus
    created_at: datetime
    updated_at: datetime


class RequestServiceCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: str = Field(..., min_length=10)
    category_id: int | None = None
    location: str | None = Field(default=None, max_length=500)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    budget_min: Decimal | None = Field(default=None, ge=0)
    budget_max: Decimal | None = Field(default=None, ge=0)
    preferred_date: date | None = None
    preferred_time: time | None = None


class RequestServiceStatusUpdateRequest(BaseModel):
    status: RequestServiceStatus
