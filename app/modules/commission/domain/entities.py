"""Entités domaine commission — ZÉRO import FastAPI/SQLAlchemy."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class CommissionType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class CommissionStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"


class EarningStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"


@dataclass
class EmployeeCommission:
    """Taux de commission d'une clinique pour un médecin (ou taux général)."""
    id: int
    clinic_id: int
    commission_rate: Decimal
    type: CommissionType
    is_active: bool = True
    doctor_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CommissionEarning:
    """Commission calculée pour un rendez-vous complété."""
    id: int
    appointment_id: int
    clinic_id: int
    doctor_id: int
    appointment_amount: Decimal
    commission_rate: Decimal
    commission_amount: Decimal
    doctor_earning: Decimal
    status: CommissionStatus = CommissionStatus.PENDING
    paid_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_paid(self) -> None:
        self.status = CommissionStatus.PAID
        self.paid_at = datetime.utcnow()

    @staticmethod
    def calculate(
        appointment_amount: Decimal,
        commission_rate: Decimal,
        commission_type: CommissionType,
    ) -> tuple[Decimal, Decimal]:
        """Retourne (commission_amount, doctor_earning)."""
        if commission_type == CommissionType.PERCENTAGE:
            commission_amount = (appointment_amount * commission_rate / Decimal("100")).quantize(
                Decimal("0.01")
            )
        else:
            commission_amount = commission_rate.quantize(Decimal("0.01"))
        doctor_earning = appointment_amount - commission_amount
        return commission_amount, doctor_earning


@dataclass
class EmployeeEarning:
    """Rapport agrégé des revenus d'un médecin pour une période."""
    id: int
    doctor_id: int
    period_start: date
    period_end: date
    total_appointments: int
    gross_amount: Decimal
    commission_deducted: Decimal
    net_amount: Decimal
    status: EarningStatus = EarningStatus.PENDING
    paid_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
