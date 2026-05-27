"""Cas d'utilisation du module billing."""
from __future__ import annotations

import random
import string
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from app.core.pdf.invoice_generator import InvoiceGenerator
from app.modules.billing.domain.entities import BillingRecord, BillingStatus
from app.modules.billing.domain.exceptions import (
    BillingNotFoundError,
    InvoiceAlreadyExistsError,
    InvalidStatusTransitionError,
)
from app.modules.billing.domain.repositories import BillingRepository
from app.shared.schemas.pagination import Page, PaginationParams


def _generate_reference() -> str:
    """Génère une référence facture INV-{YYYYMMDD}-{6 chiffres aléatoires}."""
    date_part = datetime.utcnow().strftime("%Y%m%d")
    rand_part = "".join(random.choices(string.digits, k=6))
    return f"INV-{date_part}-{rand_part}"


class GetOrCreateInvoiceUseCase:
    """Récupère la facture d'un RDV ou la crée automatiquement si absente."""

    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        appointment_id: int,
        patient_id: int,
        consultation_fee: Decimal,
        tax_rate: Decimal = Decimal("0"),
        discount_amount: Decimal = Decimal("0"),
        notes: Optional[str] = None,
    ) -> BillingRecord:
        existing = await self._repo.get_by_appointment(appointment_id)
        if existing and existing.status != BillingStatus.CANCELLED:
            return existing

        subtotal = consultation_fee
        tax_amount = (subtotal * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
        total = BillingRecord.calculate_total(subtotal, discount_amount, tax_amount)
        reference = _generate_reference()
        due_date = (datetime.utcnow() + timedelta(days=30)).date()

        return await self._repo.create(
            appointment_id=appointment_id,
            patient_id=patient_id,
            reference=reference,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total=total,
            items=[
                {
                    "description": "Consultation médicale",
                    "quantity": 1,
                    "unit_price": float(consultation_fee),
                    "subtotal": float(subtotal),
                    "tax_rate": float(tax_rate),
                }
            ],
            due_date=due_date,
            notes=notes,
        )


class CreateInvoiceUseCase:
    """Crée ou remplace une facture pour un RDV."""

    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        appointment_id: int,
        patient_id: int,
        items: list[dict],
        discount_amount: Decimal = Decimal("0"),
        notes: Optional[str] = None,
    ) -> BillingRecord:
        existing = await self._repo.get_by_appointment(appointment_id)
        if existing and existing.status not in (BillingStatus.CANCELLED, BillingStatus.DRAFT):
            raise InvoiceAlreadyExistsError(appointment_id)

        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        for item in items:
            q = Decimal(str(item.get("quantity", 1)))
            up = Decimal(str(item["unit_price"]))
            tr = Decimal(str(item.get("tax_rate", 0)))
            item_subtotal = (q * up).quantize(Decimal("0.01"))
            item["subtotal"] = float(item_subtotal)
            subtotal += item_subtotal
            tax_amount += (item_subtotal * tr / Decimal("100")).quantize(Decimal("0.01"))

        total = BillingRecord.calculate_total(subtotal, discount_amount, tax_amount)
        reference = _generate_reference()
        due_date = (datetime.utcnow() + timedelta(days=30)).date()

        return await self._repo.create(
            appointment_id=appointment_id,
            patient_id=patient_id,
            reference=reference,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total=total,
            items=items,
            due_date=due_date,
            notes=notes,
        )


class GetBillingUseCase:
    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo

    async def execute(self, billing_id: int) -> BillingRecord:
        record = await self._repo.get_by_id(billing_id)
        if record is None:
            raise BillingNotFoundError(billing_id)
        return record


class GenerateInvoicePDFUseCase:
    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo
        self._generator = InvoiceGenerator()

    async def execute(self, billing_id: int, patient_name: str = "Patient") -> bytes:
        record = await self._repo.get_by_id(billing_id)
        if record is None:
            raise BillingNotFoundError(billing_id)

        items_data = [
            {
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "tax_rate": float(item.tax_rate),
                "subtotal": float(item.subtotal),
            }
            for item in record.items
        ]

        billing_data = {
            "reference": record.reference,
            "patient_name": patient_name,
            "issued_date": record.created_at.strftime("%d/%m/%Y"),
            "due_date": record.due_date.strftime("%d/%m/%Y") if record.due_date else None,
            "status": record.status.value,
            "items": items_data,
            "subtotal": float(record.subtotal),
            "discount_amount": float(record.discount_amount),
            "tax_amount": float(record.tax_amount),
            "total": float(record.total),
            "notes": record.notes,
        }
        return self._generator.generate(billing_data)


class ListMyInvoicesUseCase:
    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo

    async def execute(self, patient_id: int, params: PaginationParams) -> Page:
        records, total = await self._repo.list_by_patient(patient_id, params)
        return Page.create(records, total, params)


class AdminListBillingUseCase:
    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo

    async def execute(self, params: PaginationParams) -> Page:
        records, total = await self._repo.list_all(params)
        return Page.create(records, total, params)


class AdminUpdateBillingStatusUseCase:
    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo

    async def execute(self, billing_id: int, new_status: str) -> BillingRecord:
        record = await self._repo.get_by_id(billing_id)
        if record is None:
            raise BillingNotFoundError(billing_id)

        valid_transitions: dict[BillingStatus, list[str]] = {
            BillingStatus.DRAFT: ["issued", "cancelled"],
            BillingStatus.ISSUED: ["paid", "cancelled"],
            BillingStatus.PAID: [],
            BillingStatus.CANCELLED: [],
        }
        allowed = valid_transitions.get(record.status, [])
        if new_status not in allowed:
            raise InvalidStatusTransitionError(record.status.value, new_status)

        paid_at = datetime.utcnow() if new_status == "paid" else None
        updated = await self._repo.update_status(billing_id, new_status, paid_at)
        if updated is None:
            raise BillingNotFoundError(billing_id)
        return updated


class AdminBillingStatsUseCase:
    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo

    async def execute(self) -> dict:
        return await self._repo.get_stats()
