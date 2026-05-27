"""ABCs (ports) des repositories billing."""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from app.modules.billing.domain.entities import BillingRecord
from app.shared.schemas.pagination import PaginationParams


class BillingRepository(ABC):
    @abstractmethod
    async def get_by_id(self, billing_id: int) -> Optional[BillingRecord]: ...

    @abstractmethod
    async def get_by_appointment(self, appointment_id: int) -> Optional[BillingRecord]: ...

    @abstractmethod
    async def create(
        self,
        appointment_id: int,
        patient_id: int,
        reference: str,
        subtotal: Decimal,
        discount_amount: Decimal,
        tax_amount: Decimal,
        total: Decimal,
        items: list[dict],
        due_date: Optional[object] = None,
        notes: Optional[str] = None,
    ) -> BillingRecord: ...

    @abstractmethod
    async def update_status(
        self, billing_id: int, status: str, paid_at: Optional[object] = None
    ) -> Optional[BillingRecord]: ...

    @abstractmethod
    async def list_by_patient(
        self, patient_id: int, params: PaginationParams
    ) -> tuple[list[BillingRecord], int]: ...

    @abstractmethod
    async def list_all(
        self, params: PaginationParams
    ) -> tuple[list[BillingRecord], int]: ...

    @abstractmethod
    async def get_stats(self) -> dict: ...
