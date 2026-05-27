"""Cas d'utilisation du module commission."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from app.modules.commission.domain.entities import (
    CommissionEarning,
    CommissionType,
    EmployeeEarning,
)
from app.modules.commission.domain.exceptions import (
    CommissionNotFoundError,
    NoCommissionRateError,
)
from app.modules.commission.domain.repositories import (
    CommissionEarningRepository,
    CommissionRateRepository,
    EmployeeEarningRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams


class CalculateCommissionUseCase:
    """Déclenché quand un RDV passe en status='completed'."""

    def __init__(
        self,
        rate_repo: CommissionRateRepository,
        earning_repo: CommissionEarningRepository,
    ) -> None:
        self._rate_repo = rate_repo
        self._earning_repo = earning_repo

    async def execute(
        self,
        appointment_id: int,
        clinic_id: int,
        doctor_id: int,
        appointment_amount: Decimal,
    ) -> CommissionEarning:
        # 1. Récupérer le taux de commission spécifique au médecin ou le taux général
        rate_conf = await self._rate_repo.get_for_doctor(clinic_id, doctor_id)
        if rate_conf is None:
            raise NoCommissionRateError(clinic_id)

        commission_type = CommissionType(rate_conf.type)

        # 2. Calculer commission_amount et doctor_earning
        commission_amount, doctor_earning = CommissionEarning.calculate(
            appointment_amount, rate_conf.commission_rate, commission_type
        )

        # 3. Créer CommissionEarning
        return await self._earning_repo.create(
            appointment_id=appointment_id,
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            appointment_amount=appointment_amount,
            commission_rate=rate_conf.commission_rate,
            commission_amount=commission_amount,
            doctor_earning=doctor_earning,
        )


class GetDoctorEarningsUseCase:
    def __init__(self, repo: CommissionEarningRepository) -> None:
        self._repo = repo

    async def execute(self, doctor_id: int, params: PaginationParams) -> Page:
        earnings, total = await self._repo.list_by_doctor(doctor_id, params)
        return Page.create(earnings, total, params)


class GetDoctorEarningsSummaryUseCase:
    def __init__(self, repo: CommissionEarningRepository) -> None:
        self._repo = repo

    async def execute(self, doctor_id: int) -> dict:
        return await self._repo.get_summary_for_doctor(doctor_id)


class AdminListCommissionsUseCase:
    def __init__(self, repo: CommissionEarningRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        clinic_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Page:
        earnings, total = await self._repo.list_all(params, clinic_id, doctor_id, status)
        return Page.create(earnings, total, params)


class AdminMarkCommissionPaidUseCase:
    def __init__(self, repo: CommissionEarningRepository) -> None:
        self._repo = repo

    async def execute(self, commission_id: int) -> CommissionEarning:
        earning = await self._repo.mark_paid(commission_id)
        if earning is None:
            raise CommissionNotFoundError(commission_id)
        return earning


class GenerateEarningsReportUseCase:
    def __init__(
        self,
        earning_repo: EmployeeEarningRepository,
        commission_repo: CommissionEarningRepository,
    ) -> None:
        self._earning_repo = earning_repo
        self._commission_repo = commission_repo

    async def execute(
        self,
        period_start: date,
        period_end: date,
        clinic_id: int,
        doctor_id: Optional[int] = None,
    ) -> list[EmployeeEarning]:
        """Génère les rapports de revenus pour tous les médecins ou un médecin spécifique."""
        params = PaginationParams(page=1, per_page=1000)
        all_earnings, _ = await self._commission_repo.list_all(
            params, clinic_id=clinic_id, doctor_id=doctor_id, status=None
        )

        # Regrouper par médecin
        doctors: set[int] = {e.doctor_id for e in all_earnings}
        results: list[EmployeeEarning] = []

        for doc_id in doctors:
            report = await self._earning_repo.generate_for_period(
                doctor_id=doc_id,
                clinic_id=clinic_id,
                period_start=period_start,
                period_end=period_end,
            )
            results.append(report)

        return results


class AdminListEarningsUseCase:
    def __init__(self, repo: EmployeeEarningRepository) -> None:
        self._repo = repo

    async def execute(self, params: PaginationParams) -> Page:
        earnings, total = await self._repo.list_all(params)
        return Page.create(earnings, total, params)
