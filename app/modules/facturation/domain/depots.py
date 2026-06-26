"""ABCs (ports) des repositories facturation."""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from app.modules.facturation.domain.entites import BillingRecord
from app.shared.schemas.pagination import PaginationParams


class BillingRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id_facture: int) -> Optional[BillingRecord]: ...

    @abstractmethod
    async def get_by_appointment(self, id_rendez_vous: int) -> Optional[BillingRecord]: ...

    @abstractmethod
    async def create(
        self,
        id_rendez_vous: int,
        id_patient: int,
        reference: str,
        sous_total: Decimal,
        montant_remise: Decimal,
        montant_taxe: Decimal,
        total: Decimal,
        items: list[dict],
        date_echeance: Optional[object] = None,
        notes: Optional[str] = None,
    ) -> BillingRecord: ...

    @abstractmethod
    async def update_status(
        self, id_facture: int, statut: str, paye_le: Optional[object] = None
    ) -> Optional[BillingRecord]: ...

    @abstractmethod
    async def list_by_patient(
        self, id_patient: int, params: PaginationParams
    ) -> tuple[list[BillingRecord], int]: ...

    @abstractmethod
    async def list_all(
        self, params: PaginationParams
    ) -> tuple[list[BillingRecord], int]: ...

    @abstractmethod
    async def get_stats(self) -> dict: ...
