"""Schemas Pydantic v2 du module Logistic."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ShippingZoneSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ShippingZoneCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    is_active: bool = True


class ShippingZoneUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None


class ShippingRateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    zone_id: int
    name: str
    min_weight: Decimal
    max_weight: Decimal | None
    min_order_amount: Decimal
    rate: Decimal
    is_free_shipping: bool
    estimated_days_min: int
    estimated_days_max: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ShippingRateCreateRequest(BaseModel):
    zone_id: int
    name: str = Field(..., min_length=1, max_length=255)
    rate: Decimal = Field(..., ge=0)
    min_weight: Decimal = Field(default=Decimal("0"), ge=0)
    max_weight: Decimal | None = Field(default=None, ge=0)
    min_order_amount: Decimal = Field(default=Decimal("0"), ge=0)
    is_free_shipping: bool = False
    estimated_days_min: int = Field(default=1, ge=1)
    estimated_days_max: int = Field(default=3, ge=1)
    is_active: bool = True


class ShippingRateUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    rate: Decimal | None = Field(default=None, ge=0)
    min_weight: Decimal | None = Field(default=None, ge=0)
    max_weight: Decimal | None = Field(default=None, ge=0)
    min_order_amount: Decimal | None = Field(default=None, ge=0)
    is_free_shipping: bool | None = None
    estimated_days_min: int | None = Field(default=None, ge=1)
    estimated_days_max: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class ShippingCalculationSchema(BaseModel):
    """Résultat du calcul de frais de livraison."""
    rate: Decimal
    estimated_days_min: int
    estimated_days_max: int
    rate_name: str
    is_free_shipping: bool
