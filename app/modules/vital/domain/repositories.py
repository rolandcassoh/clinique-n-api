from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.modules.vital.domain.entities import VitalSigns, VitalStats
from app.shared.schemas.pagination import PaginationParams


class AbstractVitalSignsRepository(ABC):
    @abstractmethod
    async def list_by_patient(
        self, patient_id: int, params: PaginationParams
    ) -> tuple[list[VitalSigns], int]:
        ...

    @abstractmethod
    async def list_all_paginated(
        self,
        params: PaginationParams,
        patient_id: Optional[int] = None,
    ) -> tuple[list[VitalSigns], int]:
        ...

    @abstractmethod
    async def get_by_id(self, vital_id: int) -> Optional[VitalSigns]:
        ...

    @abstractmethod
    async def create(
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
        ...

    @abstractmethod
    async def update(self, vital_id: int, **kwargs) -> Optional[VitalSigns]:
        ...

    @abstractmethod
    async def soft_delete(self, vital_id: int) -> bool:
        ...

    @abstractmethod
    async def get_stats(self, patient_id: int) -> VitalStats:
        """Retourne la dernière valeur de chaque type de constante pour le patient."""
        ...
