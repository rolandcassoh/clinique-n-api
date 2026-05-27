from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PromotionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    type: str
    value: Decimal
    min_order_amount: Decimal | None
    max_discount_amount: Decimal | None
    usage_limit: int | None
    usage_count: int
    starts_at: datetime | None
    expires_at: datetime | None
    is_active: bool
    applicable_to: str
    created_at: datetime


class PromotionCreateSchema(BaseModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=255)
    type: str  # 'percentage' | 'fixed'
    value: Decimal = Field(gt=0)
    min_order_amount: Decimal | None = None
    max_discount_amount: Decimal | None = None
    usage_limit: int | None = None
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool = True
    applicable_to: str = "all"


class PromotionUpdateSchema(BaseModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=255)
    type: str
    value: Decimal = Field(gt=0)
    min_order_amount: Decimal | None = None
    max_discount_amount: Decimal | None = None
    usage_limit: int | None = None
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool = True
    applicable_to: str = "all"


class ValidatePromotionRequestSchema(BaseModel):
    code: str
    amount: Decimal = Field(gt=0)
    applicable_to: str = "all"


class ValidatePromotionResponseSchema(BaseModel):
    valid: bool
    discount_amount: float
    promotion: PromotionSchema | None
    reason: str | None = None


class PromotionUseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    promotion_id: int
    user_id: int
    order_id: int | None
    appointment_id: int | None
    discount_amount: Decimal
    used_at: datetime
    created_at: datetime
