"""ABCs (ports) des repositories commission."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Optional

from app.modules.commission.domain.entities import (
    CommissionEarning,
    EmployeeCommission,
    EmployeeEarning,
)
from app.shared.schemas.pagination import PaginationParams


class CommissionRateRepository(ABC):
    @abstractmethod
    async def get_for_doctor(
        self, clinic_id: int, doctor_id: int
    ) -> Optional[EmployeeCommission]: ...

    @abstractmethod
    async def list_all(
        self,
        params: PaginationParams,
        clinic_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> tuple[list[CommissionEarning], int]: ...


class CommissionEarningRepository(ABC):
    @abstractmethod
    async def create(
        self,
        appointment_id: int,
        clinic_id: int,
        doctor_id: int,
        appointment_amount: Decimal,
        commission_rate: Decimal,
        commission_amount: Decimal,
        doctor_earning: Decimal,
    ) -> CommissionEarning: ...

    @abstractmethod
    async def get_by_id(self, earning_id: int) -> Optional[CommissionEarning]: ...

    @abstractmethod
    async def mark_paid(self, earning_id: int) -> Optional[CommissionEarning]: ...

    @abstractmethod
    async def list_all(
        self,
        params: PaginationParams,
        clinic_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> tuple[list[CommissionEarning], int]: ...

    @abstractmethod
    async def list_by_doctor(
        self, doctor_id: int, params: PaginationParams
    ) -> tuple[list[CommissionEarning], int]: ...

    @abstractmethod
    async def get_summary_for_doctor(self, doctor_id: int) -> dict: ...


class EmployeeEarningRepository(ABC):
    @abstractmethod
    async def generate_for_period(
        self,
        doctor_id: int,
        clinic_id: int,
        period_start: date,
        period_end: date,
    ) -> EmployeeEarning: ...

    @abstractmethod
    async def list_all(
        self, params: PaginationParams
    ) -> tuple[list[EmployeeEarning], int]: ...

    @abstractmethod
    async def list_by_doctor(
        self, doctor_id: int, params: PaginationParams
    ) -> tuple[list[EmployeeEarning], int]: ...
