"""Schémas Pydantic v2 pour l'API appointment."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.appointment.domain.entities import AppointmentStatus, AppointmentType, PaymentStatus


# ---------------------------------------------------------------------------
# Requêtes
# ---------------------------------------------------------------------------


class BookAppointmentRequest(BaseModel):
    clinic_id: int
    doctor_id: int
    scheduled_at: datetime
    type: AppointmentType = AppointmentType.IN_PERSON
    payment_gateway: Optional[str] = None
    notes: Optional[str] = None
    is_followup: bool = False
    parent_appointment_id: Optional[int] = None
    # Champs optionnels que le client peut passer (sinon 0 par défaut)
    consultation_fee: Decimal = Field(default=Decimal("0"), ge=0)
    session_duration: int = Field(default=30, ge=10, le=240)


class PayAppointmentRequest(BaseModel):
    gateway: str = Field(..., description="stripe | razorpay | paypal | wallet")
    currency: str = Field(default="XAF", max_length=3)


class StripeIntentRequest(BaseModel):
    currency: str = Field(default="XAF", max_length=3)


class RazorpayOrderRequest(BaseModel):
    currency: str = Field(default="INR", max_length=3)


class RefundRequest(BaseModel):
    amount: Optional[Decimal] = Field(default=None, ge=0)


class ForceStatusRequest(BaseModel):
    status: AppointmentStatus


class CancelRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)


# ---------------------------------------------------------------------------
# Réponses
# ---------------------------------------------------------------------------


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference: str
    clinic_id: int
    doctor_id: int
    patient_id: int
    scheduled_at: datetime
    duration_minutes: int
    status: AppointmentStatus
    type: AppointmentType
    amount: Decimal
    advance_amount: Decimal
    payment_status: PaymentStatus
    payment_gateway: Optional[str] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    is_followup: bool
    parent_appointment_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class CancellationResponse(BaseModel):
    message: str
    is_full_refund: bool
    refund_amount: Decimal
    policy_applied: str


class PaymentStatusResponse(BaseModel):
    appointment_id: int
    payment_status: str
    payment_gateway: Optional[str]
    amount: str
    transactions: list[dict]


class StatsResponse(BaseModel):
    by_status: dict[str, int]
    total_revenue: str


class StripeIntentResponse(BaseModel):
    client_secret: Optional[str]
    payment_intent_id: str


class RazorpayOrderResponse(BaseModel):
    order_id: str
    amount: str
    currency: str
