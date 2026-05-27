"""Interfaces (ABC) des repositories RequestService."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, time
from decimal import Decimal

from app.modules.request_service.domain.entities import RequestService, RequestServiceStatus
from app.shared.schemas.pagination import PaginationParams


class RequestServiceRepository(ABC):
    @abstractmethod
    async def list_by_user(
        self, user_id: int, params: PaginationParams
    ) -> tuple[list[RequestService], int]: ...

    @abstractmethod
    async def list_all(
        self, params: PaginationParams, status: RequestServiceStatus | None = None
    ) -> tuple[list[RequestService], int]: ...

    @abstractmethod
    async def get_by_id(self, request_id: int) -> RequestService | None: ...

    @abstractmethod
    async def create(
        self,
        user_id: int,
        title: str,
        description: str,
        category_id: int | None,
        location: str | None,
        latitude: Decimal | None,
        longitude: Decimal | None,
        budget_min: Decimal | None,
        budget_max: Decimal | None,
        preferred_date: date | None,
        preferred_time: time | None,
    ) -> RequestService: ...

    @abstractmethod
    async def update_status(
        self, request_id: int, new_status: RequestServiceStatus
    ) -> RequestService | None: ...

    @abstractmethod
    async def soft_delete(self, request_id: int) -> bool: ...
