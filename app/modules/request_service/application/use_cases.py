"""Use Cases du module RequestService."""
from __future__ import annotations

from datetime import date, time
from decimal import Decimal

from app.modules.request_service.domain.entities import RequestService, RequestServiceStatus
from app.modules.request_service.domain.exceptions import (
    RequestServiceAccessDeniedError,
    RequestServiceCannotCancelError,
    RequestServiceNotFoundError,
)
from app.modules.request_service.domain.repositories import RequestServiceRepository
from app.shared.schemas.pagination import Page, PaginationParams


class CreateRequestServiceUseCase:
    def __init__(self, repo: RequestServiceRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        user_id: int,
        title: str,
        description: str,
        category_id: int | None = None,
        location: str | None = None,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        budget_min: Decimal | None = None,
        budget_max: Decimal | None = None,
        preferred_date: date | None = None,
        preferred_time: time | None = None,
    ) -> RequestService:
        return await self._repo.create(
            user_id=user_id, title=title, description=description,
            category_id=category_id, location=location, latitude=latitude,
            longitude=longitude, budget_min=budget_min, budget_max=budget_max,
            preferred_date=preferred_date, preferred_time=preferred_time,
        )


class ListMyRequestServicesUseCase:
    def __init__(self, repo: RequestServiceRepository) -> None:
        self._repo = repo

    async def execute(
        self, user_id: int, params: PaginationParams
    ) -> Page[RequestService]:
        items, total = await self._repo.list_by_user(user_id, params)
        return Page.create(data=items, total=total, params=params)


class GetMyRequestServiceUseCase:
    def __init__(self, repo: RequestServiceRepository) -> None:
        self._repo = repo

    async def execute(self, request_id: int, user_id: int) -> RequestService:
        req = await self._repo.get_by_id(request_id)
        if req is None:
            raise RequestServiceNotFoundError(request_id)
        if req.user_id != user_id:
            raise RequestServiceAccessDeniedError(request_id)
        return req


class CancelRequestServiceUseCase:
    def __init__(self, repo: RequestServiceRepository) -> None:
        self._repo = repo

    async def execute(self, request_id: int, user_id: int) -> None:
        req = await self._repo.get_by_id(request_id)
        if req is None:
            raise RequestServiceNotFoundError(request_id)
        if req.user_id != user_id:
            raise RequestServiceAccessDeniedError(request_id)
        if not req.can_cancel:
            raise RequestServiceCannotCancelError(request_id, req.status.value)
        await self._repo.soft_delete(request_id)


class ListAllRequestServicesUseCase:
    def __init__(self, repo: RequestServiceRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        status: RequestServiceStatus | None = None,
    ) -> Page[RequestService]:
        items, total = await self._repo.list_all(params, status=status)
        return Page.create(data=items, total=total, params=params)


class UpdateRequestServiceStatusUseCase:
    def __init__(self, repo: RequestServiceRepository) -> None:
        self._repo = repo

    async def execute(
        self, request_id: int, new_status: RequestServiceStatus
    ) -> RequestService:
        req = await self._repo.update_status(request_id, new_status)
        if req is None:
            raise RequestServiceNotFoundError(request_id)
        return req
