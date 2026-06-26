"""ABCs (ports) des repositories du module commission."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Optional

from app.modules.commission.domain.entites import (
    CommissionEarning,
    EmployeeCommission,
    EmployeeEarning,
)
from app.shared.schemas.pagination import PaginationParams


class CommissionRateRepository(ABC):
    @abstractmethod
    async def get_for_doctor(
        self, id_clinique: int, id_medecin: int
    ) -> Optional[EmployeeCommission]: ...

    @abstractmethod
    async def list_all(
        self,
        params: PaginationParams,
        id_clinique: Optional[int] = None,
        id_medecin: Optional[int] = None,
        statut: Optional[str] = None,
    ) -> tuple[list[CommissionEarning], int]: ...


class CommissionEarningRepository(ABC):
    @abstractmethod
    async def create(
        self,
        id_rendez_vous: int,
        id_clinique: int,
        id_medecin: int,
        montant_rdv: Decimal,
        taux_commission: Decimal,
        montant_commission: Decimal,
        gain_medecin: Decimal,
    ) -> CommissionEarning: ...

    @abstractmethod
    async def get_by_id(self, earning_id: int) -> Optional[CommissionEarning]: ...

    @abstractmethod
    async def mark_paid(self, earning_id: int) -> Optional[CommissionEarning]: ...

    @abstractmethod
    async def list_all(
        self,
        params: PaginationParams,
        id_clinique: Optional[int] = None,
        id_medecin: Optional[int] = None,
        statut: Optional[str] = None,
    ) -> tuple[list[CommissionEarning], int]: ...

    @abstractmethod
    async def list_by_doctor(
        self, id_medecin: int, params: PaginationParams
    ) -> tuple[list[CommissionEarning], int]: ...

    @abstractmethod
    async def get_summary_for_doctor(self, id_medecin: int) -> dict: ...


class EmployeeEarningRepository(ABC):
    @abstractmethod
    async def generate_for_period(
        self,
        id_medecin: int,
        id_clinique: int,
        debut_periode: date,
        fin_periode: date,
    ) -> EmployeeEarning: ...

    @abstractmethod
    async def list_all(
        self, params: PaginationParams
    ) -> tuple[list[EmployeeEarning], int]: ...

    @abstractmethod
    async def list_by_doctor(
        self, id_medecin: int, params: PaginationParams
    ) -> tuple[list[EmployeeEarning], int]: ...
