"""Cas d'utilisation du module encounter."""
from __future__ import annotations

import structlog
from typing import Optional

from app.modules.encounter.domain.entities import (
    BodyChart,
    MedicalReport,
    PatientEncounter,
    Prescription,
)
from app.modules.encounter.domain.exceptions import (
    EncounterNotFoundError,
    MedicalReportNotFoundError,
    PrescriptionNotFoundError,
    UnauthorizedMedicalAccessError,
)
from app.modules.encounter.domain.repositories import (
    BodyChartRepository,
    EncounterRepository,
    MedicalReportRepository,
    PrescriptionRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams

logger = structlog.get_logger()


class CreateEncounterUseCase:
    def __init__(self, repo: EncounterRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        doctor_id: int,
        patient_id: int,
        appointment_id: Optional[int] = None,
        chief_complaint: Optional[str] = None,
    ) -> PatientEncounter:
        return await self._repo.create(
            doctor_id=doctor_id,
            patient_id=patient_id,
            appointment_id=appointment_id,
            chief_complaint=chief_complaint,
        )


class GetEncounterUseCase:
    def __init__(self, repo: EncounterRepository) -> None:
        self._repo = repo

    async def execute(self, encounter_id: int) -> PatientEncounter:
        enc = await self._repo.get_by_id(encounter_id)
        if enc is None:
            raise EncounterNotFoundError(encounter_id)
        return enc


class UpdateEncounterUseCase:
    def __init__(self, repo: EncounterRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        encounter_id: int,
        follow_up_date: Optional[object] = None,
        follow_up_notes: Optional[str] = None,
        status: Optional[str] = None,
    ) -> PatientEncounter:
        enc = await self._repo.update(encounter_id, follow_up_date, follow_up_notes, status)
        if enc is None:
            raise EncounterNotFoundError(encounter_id)
        return enc


class GetMedicalReportUseCase:
    """Récupère le rapport médical — réservé au médecin traitant."""

    def __init__(self, repo: MedicalReportRepository, enc_repo: EncounterRepository) -> None:
        self._repo = repo
        self._enc_repo = enc_repo

    async def execute(self, encounter_id: int, requesting_doctor_id: int) -> MedicalReport:
        enc = await self._enc_repo.get_by_id(encounter_id)
        if enc is None:
            raise EncounterNotFoundError(encounter_id)
        if enc.doctor_id != requesting_doctor_id:
            raise UnauthorizedMedicalAccessError()
        report = await self._repo.get_by_encounter(encounter_id)
        if report is None:
            raise MedicalReportNotFoundError(encounter_id)
        logger.info(
            "medical_data.accessed",
            encounter_id=encounter_id,
            doctor_id=requesting_doctor_id,
        )
        return report


class UpsertMedicalReportUseCase:
    def __init__(self, repo: MedicalReportRepository, enc_repo: EncounterRepository) -> None:
        self._repo = repo
        self._enc_repo = enc_repo

    async def execute(
        self,
        encounter_id: int,
        requesting_doctor_id: int,
        symptoms: Optional[str] = None,
        diagnosis: Optional[str] = None,
        treatment: Optional[str] = None,
        blood_pressure: Optional[str] = None,
        temperature: Optional[str] = None,
        weight: Optional[str] = None,
        additional_notes: Optional[str] = None,
    ) -> MedicalReport:
        enc = await self._enc_repo.get_by_id(encounter_id)
        if enc is None:
            raise EncounterNotFoundError(encounter_id)
        if enc.doctor_id != requesting_doctor_id:
            raise UnauthorizedMedicalAccessError()
        return await self._repo.upsert(
            encounter_id=encounter_id,
            symptoms=symptoms,
            diagnosis=diagnosis,
            treatment=treatment,
            blood_pressure=blood_pressure,
            temperature=temperature,
            weight=weight,
            additional_notes=additional_notes,
        )


class ListPrescriptionsUseCase:
    def __init__(self, repo: PrescriptionRepository) -> None:
        self._repo = repo

    async def execute(self, encounter_id: int) -> list[Prescription]:
        return await self._repo.list_by_encounter(encounter_id)


class CreatePrescriptionUseCase:
    def __init__(self, repo: PrescriptionRepository, enc_repo: EncounterRepository) -> None:
        self._repo = repo
        self._enc_repo = enc_repo

    async def execute(
        self,
        encounter_id: int,
        requesting_doctor_id: int,
        medication_name: str,
        dosage: Optional[str] = None,
        frequency: Optional[str] = None,
        duration_days: Optional[int] = None,
        instructions: Optional[str] = None,
        is_chronic: bool = False,
    ) -> Prescription:
        enc = await self._enc_repo.get_by_id(encounter_id)
        if enc is None:
            raise EncounterNotFoundError(encounter_id)
        if enc.doctor_id != requesting_doctor_id:
            raise UnauthorizedMedicalAccessError()
        return await self._repo.create(
            encounter_id=encounter_id,
            medication_name=medication_name,
            dosage=dosage,
            frequency=frequency,
            duration_days=duration_days,
            instructions=instructions,
            is_chronic=is_chronic,
        )


class DeletePrescriptionUseCase:
    def __init__(self, repo: PrescriptionRepository) -> None:
        self._repo = repo

    async def execute(self, prescription_id: int) -> None:
        deleted = await self._repo.soft_delete(prescription_id)
        if not deleted:
            raise PrescriptionNotFoundError(prescription_id)


class ListMyEncountersUseCase:
    def __init__(self, repo: EncounterRepository) -> None:
        self._repo = repo

    async def execute(self, patient_id: int, params: PaginationParams) -> Page:
        encounters, total = await self._repo.list_by_patient(patient_id, params)
        return Page.create(encounters, total, params)


class ListMyPrescriptionsUseCase:
    def __init__(self, repo: PrescriptionRepository) -> None:
        self._repo = repo

    async def execute(self, patient_id: int) -> list[Prescription]:
        return await self._repo.list_active_by_patient(patient_id)


class GetBodyChartUseCase:
    def __init__(self, repo: BodyChartRepository) -> None:
        self._repo = repo

    async def execute(self, appointment_id: int) -> BodyChart:
        chart = await self._repo.get_by_appointment(appointment_id)
        if chart is None:
            from app.modules.encounter.domain.exceptions import BodyChartNotFoundError
            raise BodyChartNotFoundError(appointment_id)
        return chart


class UpsertBodyChartUseCase:
    def __init__(self, repo: BodyChartRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        appointment_id: int,
        image_url: str,
        annotations: Optional[list] = None,
        notes: Optional[str] = None,
    ) -> BodyChart:
        return await self._repo.upsert(
            appointment_id=appointment_id,
            image_url=image_url,
            annotations=annotations,
            notes=notes,
        )


class AdminListEncountersUseCase:
    def __init__(self, repo: EncounterRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        patient_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
    ) -> Page:
        encounters, total = await self._repo.list_all(params, patient_id, doctor_id)
        return Page.create(encounters, total, params)
