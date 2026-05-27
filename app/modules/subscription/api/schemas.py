"""Pydantic v2 schemas — module subscription."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PlanLimitationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    feature: str
    value: str
    created_at: datetime


class SubscriptionPlanSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: Optional[str]
    price: Decimal
    billing_period: str
    trial_days: int
    is_active: bool
    is_featured: bool
    sort_order: int
    created_at: datetime
    limitations: list[PlanLimitationSchema] = []


class SubscriptionPlanCreateSchema(BaseModel):
    name: str
    slug: str
    price: float
    billing_period: str = "monthly"
    description: Optional[str] = None
    trial_days: int = 0
    is_featured: bool = False
    sort_order: int = 0


class SubscriptionPlanUpdateSchema(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    price: Optional[float] = None
    billing_period: Optional[str] = None
    description: Optional[str] = None
    trial_days: Optional[int] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    sort_order: Optional[int] = None


class PlanLimitationUpsertSchema(BaseModel):
    feature: str
    value: str


class SubscriptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clinic_id: int
    plan_id: int
    status: str
    starts_at: datetime
    ends_at: datetime
    auto_renew: bool
    cancelled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class SubscribeSchema(BaseModel):
    plan_id: int
    clinic_id: int


class RenewSchema(BaseModel):
    plan_id: Optional[int] = None


class ForceStatusSchema(BaseModel):
    status: str
