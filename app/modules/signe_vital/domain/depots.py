from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.modules.signe_vital.domain.entites import VitalSigns, VitalStats
from app.shared.schemas.pagination import PaginationParams


class AbstractVitalSignsRepository(ABC):
    @abstractmethod
    async def list_by_patient(
        self, id_patient: int, params: PaginationParams
    ) -> tuple[list[VitalSigns], int]:
        ...

    @abstractmethod
    async def list_all_paginated(
        self,
        params: PaginationParams,
        id_patient: Optional[int] = None,
    ) -> tuple[list[VitalSigns], int]:
        ...

    @abstractmethod
    async def get_by_id(self, vital_id: int) -> Optional[VitalSigns]:
        ...

    @abstractmethod
    async def create(
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
        ...

    @abstractmethod
    async def update(self, vital_id: int, **kwargs) -> Optional[VitalSigns]:
        ...

    @abstractmethod
    async def soft_delete(self, vital_id: int) -> bool:
        ...

    @abstractmethod
    async def get_stats(self, id_patient: int) -> VitalStats:
        """Retourne la dernière valeur de chaque type de constante pour le patient."""
        ...
