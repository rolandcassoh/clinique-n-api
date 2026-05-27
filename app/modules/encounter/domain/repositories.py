"""ABCs (ports) des repositories encounter."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.encounter.domain.entities import (
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
        doctor_id: int,
        patient_id: int,
        appointment_id: Optional[int],
        chief_complaint: Optional[str],
    ) -> PatientEncounter: ...

    @abstractmethod
    async def get_by_id(self, encounter_id: int) -> Optional[PatientEncounter]: ...

    @abstractmethod
    async def update(
        self,
        encounter_id: int,
        follow_up_date: Optional[object],
        follow_up_notes: Optional[str],
        status: Optional[str],
    ) -> Optional[PatientEncounter]: ...

    @abstractmethod
    async def list_by_patient(
        self, patient_id: int, params: PaginationParams
    ) -> tuple[list[PatientEncounter], int]: ...

    @abstractmethod
    async def list_all(
        self,
        params: PaginationParams,
        patient_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
    ) -> tuple[list[PatientEncounter], int]: ...


class MedicalReportRepository(ABC):
    @abstractmethod
    async def get_by_encounter(self, encounter_id: int) -> Optional[MedicalReport]: ...

    @abstractmethod
    async def upsert(
        self,
        encounter_id: int,
        symptoms: Optional[str],
        diagnosis: Optional[str],
        treatment: Optional[str],
        blood_pressure: Optional[str],
        temperature: Optional[str],
        weight: Optional[str],
        additional_notes: Optional[str],
    ) -> MedicalReport: ...


class PrescriptionRepository(ABC):
    @abstractmethod
    async def list_by_encounter(self, encounter_id: int) -> list[Prescription]: ...

    @abstractmethod
    async def list_active_by_patient(self, patient_id: int) -> list[Prescription]: ...

    @abstractmethod
    async def create(
        self,
        encounter_id: int,
        medication_name: str,
        dosage: Optional[str],
        frequency: Optional[str],
        duration_days: Optional[int],
        instructions: Optional[str],
        is_chronic: bool,
    ) -> Prescription: ...

    @abstractmethod
    async def soft_delete(self, prescription_id: int) -> bool: ...


class BodyChartRepository(ABC):
    @abstractmethod
    async def get_by_appointment(self, appointment_id: int) -> Optional[BodyChart]: ...

    @abstractmethod
    async def upsert(
        self,
        appointment_id: int,
        image_url: str,
        annotations: Optional[list],
        notes: Optional[str],
    ) -> BodyChart: ...
