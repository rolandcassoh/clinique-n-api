"""Cas d'utilisation du module commission."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from app.modules.commission.domain.entites import (
    CommissionEarning,
    CommissionType,
    EmployeeEarning,
)
from app.modules.commission.domain.exceptions import (
    CommissionNotFoundError,
    NoCommissionRateError,
)
from app.modules.commission.domain.depots import (
    CommissionEarningRepository,
    CommissionRateRepository,
    EmployeeEarningRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams


class CalculateCommissionUseCase:
    """Déclenché lorsqu'un rendez-vous passe au statut 'completed'."""

    def __init__(
        self,
        rate_repo: CommissionRateRepository,
        earning_repo: CommissionEarningRepository,
    ) -> None:
        self._rate_repo = rate_repo
        self._earning_repo = earning_repo

    async def execute(
        self,
        id_rendez_vous: int,
        id_clinique: int,
        id_medecin: int,
        montant_rdv: Decimal,
    ) -> CommissionEarning:
        # 1. Récupérer le taux de commission spécifique au médecin ou le taux général de la clinique
        config_taux = await self._rate_repo.get_for_doctor(id_clinique, id_medecin)
        if config_taux is None:
            raise NoCommissionRateError(id_clinique)

        type_commission = CommissionType(config_taux.type)

        # 2. Calculer le montant de commission et le revenu du médecin
        montant_commission, revenu_medecin = CommissionEarning.calculate(
            montant_rdv, config_taux.taux_commission, type_commission
        )

        # 3. Créer l'enregistrement CommissionEarning
        return await self._earning_repo.create(
            id_rendez_vous=id_rendez_vous,
            id_clinique=id_clinique,
            id_medecin=id_medecin,
            montant_rdv=montant_rdv,
            taux_commission=config_taux.taux_commission,
            montant_commission=montant_commission,
            gain_medecin=revenu_medecin,
        )


class GetDoctorEarningsUseCase:
    def __init__(self, repo: CommissionEarningRepository) -> None:
        self._repo = repo

    async def execute(self, id_medecin: int, params: PaginationParams) -> Page:
        earnings, total = await self._repo.list_by_doctor(id_medecin, params)
        return Page.create(earnings, total, params)


class GetDoctorEarningsSummaryUseCase:
    def __init__(self, repo: CommissionEarningRepository) -> None:
        self._repo = repo

    async def execute(self, id_medecin: int) -> dict:
        return await self._repo.get_summary_for_doctor(id_medecin)


class AdminListCommissionsUseCase:
    def __init__(self, repo: CommissionEarningRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        id_clinique: Optional[int] = None,
        id_medecin: Optional[int] = None,
        statut: Optional[str] = None,
    ) -> Page:
        earnings, total = await self._repo.list_all(params, id_clinique, id_medecin, statut)
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
        debut_periode: date,
        fin_periode: date,
        id_clinique: int,
        id_medecin: Optional[int] = None,
    ) -> list[EmployeeEarning]:
        """Génère les rapports de revenus pour tous les médecins ou un médecin spécifique."""
        params = PaginationParams(page=1, per_page=1000)
        tous_revenus, _ = await self._commission_repo.list_all(
            params, id_clinique=id_clinique, id_medecin=id_medecin, statut=None
        )

        # Regrouper par médecin
        medecins: set[int] = {r.id_medecin for r in tous_revenus}
        resultats: list[EmployeeEarning] = []

        for id_medecin in medecins:
            rapport = await self._earning_repo.generate_for_period(
                id_medecin=id_medecin,
                id_clinique=id_clinique,
                debut_periode=debut_periode,
                fin_periode=fin_periode,
            )
            resultats.append(rapport)

        return resultats


class AdminListEarningsUseCase:
    def __init__(self, repo: EmployeeEarningRepository) -> None:
        self._repo = repo

    async def execute(self, params: PaginationParams) -> Page:
        earnings, total = await self._repo.list_all(params)
        return Page.create(earnings, total, params)
