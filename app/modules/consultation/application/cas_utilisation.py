"""Cas d'utilisation — module consultations médicales."""
from __future__ import annotations

import structlog
from typing import Optional

from app.modules.consultation.domain.entites import (
    BodyChart,
    MedicalReport,
    PatientEncounter,
    Prescription,
)
from app.modules.consultation.domain.exceptions import (
    EncounterNotFoundError,
    MedicalReportNotFoundError,
    PrescriptionNotFoundError,
    UnauthorizedMedicalAccessError,
)
from app.modules.consultation.domain.depots import (
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
        id_medecin: int,
        id_patient: int,
        id_rendez_vous: Optional[int] = None,
        motif_principal: Optional[str] = None,
    ) -> PatientEncounter:
        return await self._repo.create(
            id_medecin=id_medecin,
            id_patient=id_patient,
            id_rendez_vous=id_rendez_vous,
            motif_principal=motif_principal,
        )


class GetEncounterUseCase:
    def __init__(self, repo: EncounterRepository) -> None:
        self._repo = repo

    async def execute(self, id_consultation: int) -> PatientEncounter:
        consultation = await self._repo.get_by_id(id_consultation)
        if consultation is None:
            raise EncounterNotFoundError(id_consultation)
        return consultation


class UpdateEncounterUseCase:
    def __init__(self, repo: EncounterRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_consultation: int,
        date_suivi: Optional[object] = None,
        notes_suivi: Optional[str] = None,
        statut: Optional[str] = None,
    ) -> PatientEncounter:
        consultation = await self._repo.update(id_consultation, date_suivi, notes_suivi, statut)
        if consultation is None:
            raise EncounterNotFoundError(id_consultation)
        return consultation


class GetMedicalReportUseCase:
    """Récupère le rapport médical — réservé au médecin traitant."""

    def __init__(self, repo: MedicalReportRepository, enc_repo: EncounterRepository) -> None:
        self._repo = repo
        self._enc_repo = enc_repo

    async def execute(self, id_consultation: int, requesting_doctor_id: int) -> MedicalReport:
        consultation = await self._enc_repo.get_by_id(id_consultation)
        if consultation is None:
            raise EncounterNotFoundError(id_consultation)
        if consultation.id_medecin != requesting_doctor_id:
            raise UnauthorizedMedicalAccessError()
        rapport = await self._repo.get_by_encounter(id_consultation)
        if rapport is None:
            raise MedicalReportNotFoundError(id_consultation)
        logger.info(
            "donnees_medicales.accedees",
            id_consultation=id_consultation,
            id_medecin=requesting_doctor_id,
        )
        return rapport


class UpsertMedicalReportUseCase:
    def __init__(self, repo: MedicalReportRepository, enc_repo: EncounterRepository) -> None:
        self._repo = repo
        self._enc_repo = enc_repo

    async def execute(
        self,
        id_consultation: int,
        requesting_doctor_id: int,
        symptomes: Optional[str] = None,
        diagnostic: Optional[str] = None,
        traitement: Optional[str] = None,
        tension_arterielle: Optional[str] = None,
        temperature: Optional[str] = None,
        poids: Optional[str] = None,
        notes_complementaires: Optional[str] = None,
    ) -> MedicalReport:
        consultation = await self._enc_repo.get_by_id(id_consultation)
        if consultation is None:
            raise EncounterNotFoundError(id_consultation)
        if consultation.id_medecin != requesting_doctor_id:
            raise UnauthorizedMedicalAccessError()
        return await self._repo.upsert(
            id_consultation=id_consultation,
            symptomes=symptomes,
            diagnostic=diagnostic,
            traitement=traitement,
            tension_arterielle=tension_arterielle,
            temperature=temperature,
            poids=poids,
            notes_complementaires=notes_complementaires,
        )


class ListPrescriptionsUseCase:
    def __init__(self, repo: PrescriptionRepository) -> None:
        self._repo = repo

    async def execute(self, id_consultation: int) -> list[Prescription]:
        return await self._repo.list_by_encounter(id_consultation)


class CreatePrescriptionUseCase:
    def __init__(self, repo: PrescriptionRepository, enc_repo: EncounterRepository) -> None:
        self._repo = repo
        self._enc_repo = enc_repo

    async def execute(
        self,
        id_consultation: int,
        requesting_doctor_id: int,
        nom_medicament: str,
        posologie: Optional[str] = None,
        frequence: Optional[str] = None,
        duree_jours: Optional[int] = None,
        instructions: Optional[str] = None,
        est_chronique: bool = False,
    ) -> Prescription:
        consultation = await self._enc_repo.get_by_id(id_consultation)
        if consultation is None:
            raise EncounterNotFoundError(id_consultation)
        if consultation.id_medecin != requesting_doctor_id:
            raise UnauthorizedMedicalAccessError()
        return await self._repo.create(
            id_consultation=id_consultation,
            nom_medicament=nom_medicament,
            posologie=posologie,
            frequence=frequence,
            duree_jours=duree_jours,
            instructions=instructions,
            est_chronique=est_chronique,
        )


class DeletePrescriptionUseCase:
    def __init__(self, repo: PrescriptionRepository) -> None:
        self._repo = repo

    async def execute(self, prescription_id: int) -> None:
        supprime = await self._repo.soft_delete(prescription_id)
        if not supprime:
            raise PrescriptionNotFoundError(prescription_id)


class ListMyEncountersUseCase:
    def __init__(self, repo: EncounterRepository) -> None:
        self._repo = repo

    async def execute(self, id_patient: int, params: PaginationParams) -> Page:
        consultations, total = await self._repo.list_by_patient(id_patient, params)
        return Page.create(consultations, total, params)


class ListMyPrescriptionsUseCase:
    def __init__(self, repo: PrescriptionRepository) -> None:
        self._repo = repo

    async def execute(self, id_patient: int) -> list[Prescription]:
        return await self._repo.list_active_by_patient(id_patient)


class GetBodyChartUseCase:
    def __init__(self, repo: BodyChartRepository) -> None:
        self._repo = repo

    async def execute(self, id_rendez_vous: int) -> BodyChart:
        schema_anatomique = await self._repo.get_by_appointment(id_rendez_vous)
        if schema_anatomique is None:
            from app.modules.consultation.domain.exceptions import BodyChartNotFoundError
            raise BodyChartNotFoundError(id_rendez_vous)
        return schema_anatomique


class UpsertBodyChartUseCase:
    def __init__(self, repo: BodyChartRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_rendez_vous: int,
        url_image: str,
        annotations: Optional[list] = None,
        notes: Optional[str] = None,
    ) -> BodyChart:
        return await self._repo.upsert(
            id_rendez_vous=id_rendez_vous,
            url_image=url_image,
            annotations=annotations,
            notes=notes,
        )


class AdminListEncountersUseCase:
    def __init__(self, repo: EncounterRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        id_patient: Optional[int] = None,
        id_medecin: Optional[int] = None,
    ) -> Page:
        consultations, total = await self._repo.list_all(params, id_patient, id_medecin)
        return Page.create(consultations, total, params)
