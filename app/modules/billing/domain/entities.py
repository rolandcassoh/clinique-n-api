"""Entités domaine billing — ZÉRO import FastAPI/SQLAlchemy."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class BillingStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    CANCELLED = "cancelled"


@dataclass
class BillingItem:
    id: int
    billing_id: int
    description: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    tax_rate: Decimal
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BillingRecord:
    id: int
    appointment_id: int
    patient_id: int
    reference: str
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total: Decimal
    status: BillingStatus
    items: list[BillingItem] = field(default_factory=list)
    due_date: Optional[date] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_paid(self) -> None:
        if self.status == BillingStatus.CANCELLED:
            raise ValueError("Cannot mark cancelled invoice as paid")
        self.status = BillingStatus.PAID
        self.paid_at = datetime.utcnow()

    def issue(self) -> None:
        if self.status != BillingStatus.DRAFT:
            raise ValueError("Only draft invoices can be issued")
        self.status = BillingStatus.ISSUED

    def cancel(self) -> None:
        if self.status == BillingStatus.PAID:
            raise ValueError("Cannot cancel a paid invoice")
        self.status = BillingStatus.CANCELLED

    @staticmethod
    def calculate_total(
        subtotal: Decimal,
        discount_amount: Decimal,
        tax_amount: Decimal,
    ) -> Decimal:
        return subtotal - discount_amount + tax_amount
