"""Schémas Pydantic v2 du module billing."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BillingItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    billing_id: int
    description: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    tax_rate: Decimal
    created_at: datetime
    updated_at: datetime


class BillingRecordSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    patient_id: int
    reference: str
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total: Decimal
    status: str
    items: list[BillingItemSchema] = Field(default_factory=list)
    due_date: Optional[date]
    paid_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class BillingItemCreateRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(default=1, gt=0)
    unit_price: Decimal = Field(..., gt=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0)


class CreateInvoiceRequest(BaseModel):
    items: list[BillingItemCreateRequest] = Field(..., min_length=1)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = None


class GetOrCreateInvoiceRequest(BaseModel):
    patient_id: int
    consultation_fee: Decimal = Field(..., gt=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = None


class UpdateBillingStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(issued|paid|cancelled)$")


class BillingStatsSchema(BaseModel):
    total_paid: float
    total_issued: float
    counts_by_status: dict[str, int]
