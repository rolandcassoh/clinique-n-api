"""Entités domaine appointment — ZÉRO import FastAPI/SQLAlchemy."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    REFUNDED = "refunded"


class AppointmentType(str, Enum):
    IN_PERSON = "in_person"
    TELECONSULTATION = "teleconsultation"


@dataclass
class Appointment:
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
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    google_event_id: Optional[str] = None
    is_followup: bool = False
    parent_appointment_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def confirm(self) -> None:
        if self.status != AppointmentStatus.PENDING:
            raise ValueError(f"Cannot confirm appointment with status {self.status}")
        self.status = AppointmentStatus.CONFIRMED

    def complete(self) -> None:
        if self.status != AppointmentStatus.CONFIRMED:
            raise ValueError(f"Cannot complete appointment with status {self.status}")
        self.status = AppointmentStatus.COMPLETED

    def mark_no_show(self) -> None:
        if self.status != AppointmentStatus.CONFIRMED:
            raise ValueError(f"Cannot mark no_show for status {self.status}")
        self.status = AppointmentStatus.NO_SHOW

    def cancel(self, reason: str) -> None:
        if self.status == AppointmentStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed appointment")
        if self.status == AppointmentStatus.CANCELLED:
            raise ValueError("Appointment is already cancelled")
        self.status = AppointmentStatus.CANCELLED
        self.cancellation_reason = reason

    def is_cancellable_without_charge(self, now: datetime, policy_hours: int = 24) -> bool:
        """Politique d'annulation : remboursement total si > policy_hours avant le RDV."""
        delta = self.scheduled_at.replace(tzinfo=None) - now.replace(tzinfo=None)
        return delta.total_seconds() / 3600 >= policy_hours

    def calculate_refund_amount(self, now: datetime) -> Decimal:
        """Politique : >24h -> 100%, 6-24h -> 50%, <6h -> 0%."""
        hours_before = (
            self.scheduled_at.replace(tzinfo=None) - now.replace(tzinfo=None)
        ).total_seconds() / 3600
        if hours_before >= 24:
            return self.amount
        elif hours_before >= 6:
            return self.amount * Decimal("0.5")
        else:
            return Decimal("0")


@dataclass
class AppointmentTransaction:
    id: int
    appointment_id: int
    amount: Decimal
    currency: str
    gateway: str
    transaction_ref: str
    status: str  # pending | succeeded | failed | refunded
    gateway_response: Optional[dict] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DoctorSlot:
    """Représente un créneau disponible pour un médecin."""
    doctor_id: int
    scheduled_at: datetime
    duration_minutes: int = 30
    is_available: bool = True
