"""ABCs (ports) des repositories encounter."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.consultation.domain.entites import (
    BodyChart,
    MedicalReport,
    PatientEncounter,
    Prescription,
)
from app.shared.schemas.pagination import PaginationParams


class EncounterRepository(ABC):
    @abstractmethod
    async def create(
        self,
        id_medecin: int,
        id_patient: int,
        id_rendez_vous: Optional[int],
        motif_principal: Optional[str],
    ) -> PatientEncounter: ...

    @abstractmethod
    async def get_by_id(self, id_consultation: int) -> Optional[PatientEncounter]: ...

    @abstractmethod
    async def update(
        self,
        id_consultation: int,
        date_suivi: Optional[object],
        notes_suivi: Optional[str],
        statut: Optional[str],
    ) -> Optional[PatientEncounter]: ...

    @abstractmethod
    async def list_by_patient(
        self, id_patient: int, params: PaginationParams
    ) -> tuple[list[PatientEncounter], int]: ...

    @abstractmethod
    async def list_all(
        self,
        params: PaginationParams,
        id_patient: Optional[int] = None,
        id_medecin: Optional[int] = None,
    ) -> tuple[list[PatientEncounter], int]: ...


class MedicalReportRepository(ABC):
    @abstractmethod
    async def get_by_encounter(self, id_consultation: int) -> Optional[MedicalReport]: ...

    @abstractmethod
    async def upsert(
        self,
        id_consultation: int,
        symptomes: Optional[str],
        diagnostic: Optional[str],
        traitement: Optional[str],
        tension_arterielle: Optional[str],
        temperature: Optional[str],
        poids: Optional[str],
        notes_complementaires: Optional[str],
    ) -> MedicalReport: ...


class PrescriptionRepository(ABC):
    @abstractmethod
    async def list_by_encounter(self, id_consultation: int) -> list[Prescription]: ...

    @abstractmethod
    async def list_active_by_patient(self, id_patient: int) -> list[Prescription]: ...

    @abstractmethod
    async def create(
        self,
        id_consultation: int,
        nom_medicament: str,
        posologie: Optional[str],
        frequence: Optional[str],
        duree_jours: Optional[int],
        instructions: Optional[str],
        est_chronique: bool,
    ) -> Prescription: ...

    @abstractmethod
    async def soft_delete(self, prescription_id: int) -> bool: ...


class BodyChartRepository(ABC):
    @abstractmethod
    async def get_by_appointment(self, id_rendez_vous: int) -> Optional[BodyChart]: ...

    @abstractmethod
    async def upsert(
        self,
        id_rendez_vous: int,
        url_image: str,
        annotations: Optional[list],
        notes: Optional[str],
    ) -> BodyChart: ...
