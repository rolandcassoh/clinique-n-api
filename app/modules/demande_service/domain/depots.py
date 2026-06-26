"""Interfaces (ABC) des repositories RequestService."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, time
from decimal import Decimal

from app.modules.demande_service.domain.entites import RequestService, RequestServiceStatus
from app.shared.schemas.pagination import PaginationParams


class RequestServiceRepository(ABC):
    @abstractmethod
    async def list_by_user(
        self, id_utilisateur: int, params: PaginationParams
    ) -> tuple[list[RequestService], int]: ...

    @abstractmethod
    async def list_all(
        self, params: PaginationParams, statut: RequestServiceStatus | None = None
    ) -> tuple[list[RequestService], int]: ...

    @abstractmethod
    async def get_by_id(self, request_id: int) -> RequestService | None: ...

    @abstractmethod
    async def create(
        self,
        id_utilisateur: int,
        titre: str,
        description: str,
        id_categorie: int | None,
        localisation: str | None,
        latitude: Decimal | None,
        longitude: Decimal | None,
        budget_min: Decimal | None,
        budget_max: Decimal | None,
        preferred_date: date | None,
        creneau_prefere: time | None,
    ) -> RequestService: ...

    @abstractmethod
    async def update_status(
        self, request_id: int, new_status: RequestServiceStatus
    ) -> RequestService | None: ...

    @abstractmethod
    async def soft_delete(self, request_id: int) -> bool: ...
