"""Cas d'utilisation — module constantes vitales."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.modules.signe_vital.domain.entites import VitalSigns, VitalStats
from app.modules.signe_vital.domain.exceptions import (
    VitalSignsAccessDeniedError,
    VitalSignsNotFoundError,
)
from app.modules.signe_vital.domain.depots import AbstractVitalSignsRepository
from app.shared.schemas.pagination import Page, PaginationParams


class ListMyVitalsUseCase:
    def __init__(self, repo: AbstractVitalSignsRepository) -> None:
        self._repo = repo

    async def execute(self, id_patient: int, params: PaginationParams) -> Page[VitalSigns]:
        data, total = await self._repo.list_by_patient(id_patient, params)
        return Page.create(data, total, params)


class GetVitalUseCase:
    def __init__(self, repo: AbstractVitalSignsRepository) -> None:
        self._repo = repo

    async def execute(self, vital_id: int, current_user_id: int, roles: list[str]) -> VitalSigns:
        constantes = await self._repo.get_by_id(vital_id)
        if constantes is None or constantes.is_deleted:
            raise VitalSignsNotFoundError(vital_id)
        # Les patients ne voient que leurs propres constantes vitales
        est_personnel = any(r in roles for r in ["admin", "doctor", "receptionist"])
        if not est_personnel and not constantes.belongs_to(current_user_id):
            raise VitalSignsAccessDeniedError(vital_id)
        return constantes


class CreateVitalUseCase:
    def __init__(self, repo: AbstractVitalSignsRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_patient: int,
        enregistre_par: Optional[int] = None,
        id_rendez_vous: Optional[int] = None,
        tension_systolique: Optional[int] = None,
        tension_diastolique: Optional[int] = None,
        frequence_cardiaque: Optional[int] = None,
        temperature: Optional[Decimal] = None,
        poids: Optional[Decimal] = None,
        taille: Optional[Decimal] = None,
        saturation_oxygene: Optional[int] = None,
        glycemie: Optional[Decimal] = None,
        notes: Optional[str] = None,
        enregistre_le: Optional[datetime] = None,
    ) -> VitalSigns:
        return await self._repo.create(
            id_patient=id_patient,
            enregistre_par=enregistre_par,
            id_rendez_vous=id_rendez_vous,
            tension_systolique=tension_systolique,
            tension_diastolique=tension_diastolique,
            frequence_cardiaque=frequence_cardiaque,
            temperature=temperature,
            poids=poids,
            taille=taille,
            saturation_oxygene=saturation_oxygene,
            glycemie=glycemie,
            notes=notes,
            enregistre_le=enregistre_le,
        )


class UpdateVitalUseCase:
    def __init__(self, repo: AbstractVitalSignsRepository) -> None:
        self._repo = repo

    async def execute(self, vital_id: int, current_user_id: int, roles: list[str], **kwargs) -> VitalSigns:
        constantes = await self._repo.get_by_id(vital_id)
        if constantes is None or constantes.is_deleted:
            raise VitalSignsNotFoundError(vital_id)
        # Seuls les médecins et administrateurs peuvent modifier
        est_medecin = "doctor" in roles or "admin" in roles
        if not est_medecin:
            raise VitalSignsAccessDeniedError(vital_id)
        mis_a_jour = await self._repo.update(vital_id, **kwargs)
        if mis_a_jour is None:
            raise VitalSignsNotFoundError(vital_id)
        return mis_a_jour


class DeleteVitalUseCase:
    def __init__(self, repo: AbstractVitalSignsRepository) -> None:
        self._repo = repo

    async def execute(self, vital_id: int, current_user_id: int, roles: list[str]) -> None:
        constantes = await self._repo.get_by_id(vital_id)
        if constantes is None or constantes.is_deleted:
            raise VitalSignsNotFoundError(vital_id)
        est_personnel = any(r in roles for r in ["admin", "doctor"])
        if not est_personnel:
            raise VitalSignsAccessDeniedError(vital_id)
        await self._repo.soft_delete(vital_id)


class ListAdminVitalsUseCase:
    def __init__(self, repo: AbstractVitalSignsRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        id_patient: Optional[int] = None,
    ) -> Page[VitalSigns]:
        data, total = await self._repo.list_all_paginated(params, id_patient=id_patient)
        return Page.create(data, total, params)


class GetVitalStatsUseCase:
    def __init__(self, repo: AbstractVitalSignsRepository) -> None:
        self._repo = repo

    async def execute(self, id_patient: int) -> VitalStats:
        return await self._repo.get_stats(id_patient)
