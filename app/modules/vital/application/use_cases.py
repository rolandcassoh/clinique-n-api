"""Use cases — module vital."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.modules.vital.domain.entities import VitalSigns, VitalStats
from app.modules.vital.domain.exceptions import (
    VitalSignsAccessDeniedError,
    VitalSignsNotFoundError,
)
from app.modules.vital.domain.repositories import AbstractVitalSignsRepository
from app.shared.schemas.pagination import Page, PaginationParams


class ListMyVitalsUseCase:
    def __init__(self, repo: AbstractVitalSignsRepository) -> None:
        self._repo = repo

    async def execute(self, patient_id: int, params: PaginationParams) -> Page[VitalSigns]:
        data, total = await self._repo.list_by_patient(patient_id, params)
        return Page.create(data, total, params)


class GetVitalUseCase:
    def __init__(self, repo: AbstractVitalSignsRepository) -> None:
        self._repo = repo

    async def execute(self, vital_id: int, current_user_id: int, roles: list[str]) -> VitalSigns:
        vital = await self._repo.get_by_id(vital_id)
        if vital is None or vital.is_deleted:
            raise VitalSignsNotFoundError(vital_id)
        # Patients ne voient que leurs propres constantes
        is_staff = any(r in roles for r in ["admin", "doctor", "receptionist"])
        if not is_staff and not vital.belongs_to(current_user_id):
            raise VitalSignsAccessDeniedError(vital_id)
        return vital


class CreateVitalUseCase:
    def __init__(self, repo: AbstractVitalSignsRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        patient_id: int,
        recorded_by: Optional[int] = None,
        appointment_id: Optional[int] = None,
        blood_pressure_systolic: Optional[int] = None,
        blood_pressure_diastolic: Optional[int] = None,
        heart_rate: Optional[int] = None,
        temperature: Optional[Decimal] = None,
        weight: Optional[Decimal] = None,
        height: Optional[Decimal] = None,
        oxygen_saturation: Optional[int] = None,
        blood_sugar: Optional[Decimal] = None,
        notes: Optional[str] = None,
        recorded_at: Optional[datetime] = None,
    ) -> VitalSigns:
        return await self._repo.create(
            patient_id=patient_id,
            recorded_by=recorded_by,
            appointment_id=appointment_id,
            blood_pressure_systolic=blood_pressure_systolic,
            blood_pressure_diastolic=blood_pressure_diastolic,
            heart_rate=heart_rate,
            temperature=temperature,
            weight=weight,
            height=height,
            oxygen_saturation=oxygen_saturation,
            blood_sugar=blood_sugar,
            notes=notes,
            recorded_at=recorded_at,
        )


class UpdateVitalUseCase:
    def __init__(self, repo: AbstractVitalSignsRepository) -> None:
        self._repo = repo

    async def execute(self, vital_id: int, current_user_id: int, roles: list[str], **kwargs) -> VitalSigns:
        vital = await self._repo.get_by_id(vital_id)
        if vital is None or vital.is_deleted:
            raise VitalSignsNotFoundError(vital_id)
        # Seuls les médecins peuvent modifier
        is_doctor = "doctor" in roles or "admin" in roles
        if not is_doctor:
            raise VitalSignsAccessDeniedError(vital_id)
        updated = await self._repo.update(vital_id, **kwargs)
        if updated is None:
            raise VitalSignsNotFoundError(vital_id)
        return updated


class DeleteVitalUseCase:
    def __init__(self, repo: AbstractVitalSignsRepository) -> None:
        self._repo = repo

    async def execute(self, vital_id: int, current_user_id: int, roles: list[str]) -> None:
        vital = await self._repo.get_by_id(vital_id)
        if vital is None or vital.is_deleted:
            raise VitalSignsNotFoundError(vital_id)
        is_staff = any(r in roles for r in ["admin", "doctor"])
        if not is_staff:
            raise VitalSignsAccessDeniedError(vital_id)
        await self._repo.soft_delete(vital_id)


class ListAdminVitalsUseCase:
    def __init__(self, repo: AbstractVitalSignsRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        patient_id: Optional[int] = None,
    ) -> Page[VitalSigns]:
        data, total = await self._repo.list_all_paginated(params, patient_id=patient_id)
        return Page.create(data, total, params)


class GetVitalStatsUseCase:
    def __init__(self, repo: AbstractVitalSignsRepository) -> None:
        self._repo = repo

    async def execute(self, patient_id: int) -> VitalStats:
        return await self._repo.get_stats(patient_id)
