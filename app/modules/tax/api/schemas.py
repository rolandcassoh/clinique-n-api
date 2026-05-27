from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TaxSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    rate: Decimal
    type: str
    country_id: int | None
    is_default: bool
    is_active: bool
    created_at: datetime


class TaxCreateSchema(BaseModel):
    name: str = Field(max_length=100)
    rate: Decimal = Field(ge=0)
    type: str = "percentage"
    country_id: int | None = None
    is_default: bool = False
    is_active: bool = True


class TaxUpdateSchema(BaseModel):
    name: str = Field(max_length=100)
    rate: Decimal = Field(ge=0)
    type: str = "percentage"
    country_id: int | None = None
    is_default: bool = False
    is_active: bool = True
