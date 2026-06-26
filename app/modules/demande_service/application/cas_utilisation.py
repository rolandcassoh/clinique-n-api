"""Use Cases du module RequestService."""
from __future__ import annotations

from datetime import date, time
from decimal import Decimal

from app.modules.demande_service.domain.entites import RequestService, RequestServiceStatus
from app.modules.demande_service.domain.exceptions import (
    RequestServiceAccessDeniedError,
    RequestServiceCannotCancelError,
    RequestServiceNotFoundError,
)
from app.modules.demande_service.domain.depots import RequestServiceRepository
from app.shared.schemas.pagination import Page, PaginationParams


class CreateRequestServiceUseCase:
    def __init__(self, repo: RequestServiceRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_utilisateur: int,
        titre: str,
        description: str,
        id_categorie: int | None = None,
        localisation: str | None = None,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        budget_min: Decimal | None = None,
        budget_max: Decimal | None = None,
        preferred_date: date | None = None,
        creneau_prefere: time | None = None,
    ) -> RequestService:
        return await self._repo.create(
            id_utilisateur=id_utilisateur, titre=titre, description=description,
            id_categorie=id_categorie, localisation=localisation, latitude=latitude,
            longitude=longitude, budget_min=budget_min, budget_max=budget_max,
            preferred_date=preferred_date, creneau_prefere=creneau_prefere,
        )


class ListMyRequestServicesUseCase:
    def __init__(self, repo: RequestServiceRepository) -> None:
        self._repo = repo

    async def execute(
        self, id_utilisateur: int, params: PaginationParams
    ) -> Page[RequestService]:
        items, total = await self._repo.list_by_user(id_utilisateur, params)
        return Page.create(data=items, total=total, params=params)


class GetMyRequestServiceUseCase:
    def __init__(self, repo: RequestServiceRepository) -> None:
        self._repo = repo

    async def execute(self, request_id: int, id_utilisateur: int) -> RequestService:
        req = await self._repo.get_by_id(request_id)
        if req is None:
            raise RequestServiceNotFoundError(request_id)
        if req.id_utilisateur != id_utilisateur:
            raise RequestServiceAccessDeniedError(request_id)
        return req


class CancelRequestServiceUseCase:
    def __init__(self, repo: RequestServiceRepository) -> None:
        self._repo = repo

    async def execute(self, request_id: int, id_utilisateur: int) -> None:
        req = await self._repo.get_by_id(request_id)
        if req is None:
            raise RequestServiceNotFoundError(request_id)
        if req.id_utilisateur != id_utilisateur:
            raise RequestServiceAccessDeniedError(request_id)
        if not req.can_cancel:
            raise RequestServiceCannotCancelError(request_id, req.statut.valeur)
        await self._repo.soft_delete(request_id)


class ListAllRequestServicesUseCase:
    def __init__(self, repo: RequestServiceRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        statut: RequestServiceStatus | None = None,
    ) -> Page[RequestService]:
        items, total = await self._repo.list_all(params, statut=statut)
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
