"""Implémentation SQLAlchemy async du repository RequestService."""
from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.request_service.domain.entities import RequestService, RequestServiceStatus
from app.modules.request_service.domain.repositories import RequestServiceRepository
from app.modules.request_service.infrastructure.models import RequestServiceModel
from app.shared.schemas.pagination import PaginationParams


def _to_entity(m: RequestServiceModel) -> RequestService:
    return RequestService(
        id=m.id,
        user_id=m.user_id,
        category_id=m.category_id,
        title=m.title,
        description=m.description,
        location=m.location,
        latitude=m.latitude,
        longitude=m.longitude,
        budget_min=m.budget_min,
        budget_max=m.budget_max,
        preferred_date=m.preferred_date,  # type: ignore[arg-type]
        preferred_time=m.preferred_time,  # type: ignore[arg-type]
        status=RequestServiceStatus(m.status),
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyRequestServiceRepository(RequestServiceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_user(
        self, user_id: int, params: PaginationParams
    ) -> tuple[list[RequestService], int]:
        base_q = select(RequestServiceModel).where(
            RequestServiceModel.user_id == user_id,
            RequestServiceModel.deleted_at.is_(None),
        )
        count_q = select(func.count()).select_from(base_q.subquery())
        total: int = (await self._session.execute(count_q)).scalar_one()
        rows_q = base_q.order_by(RequestServiceModel.id.desc()).offset(params.offset).limit(params.per_page)
        rows = (await self._session.execute(rows_q)).scalars().all()
        return [_to_entity(r) for r in rows], total

    async def list_all(
        self, params: PaginationParams, status: RequestServiceStatus | None = None
    ) -> tuple[list[RequestService], int]:
        base_q = select(RequestServiceModel).where(
            RequestServiceModel.deleted_at.is_(None),
        )
        if status is not None:
            base_q = base_q.where(RequestServiceModel.status == status.value)
        count_q = select(func.count()).select_from(base_q.subquery())
        total: int = (await self._session.execute(count_q)).scalar_one()
        rows_q = base_q.order_by(RequestServiceModel.id.desc()).offset(params.offset).limit(params.per_page)
        rows = (await self._session.execute(rows_q)).scalars().all()
        return [_to_entity(r) for r in rows], total

    async def get_by_id(self, request_id: int) -> RequestService | None:
        q = select(RequestServiceModel).where(
            RequestServiceModel.id == request_id,
            RequestServiceModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _to_entity(row) if row else None

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
    ) -> RequestService:
        m = RequestServiceModel(
            user_id=user_id,
            title=title,
            description=description,
            category_id=category_id,
            location=location,
            latitude=latitude,
            longitude=longitude,
            budget_min=budget_min,
            budget_max=budget_max,
            preferred_date=preferred_date,
            preferred_time=preferred_time,
            status=RequestServiceStatus.PENDING.value,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_entity(m)

    async def update_status(
        self, request_id: int, new_status: RequestServiceStatus
    ) -> RequestService | None:
        q = select(RequestServiceModel).where(
            RequestServiceModel.id == request_id,
            RequestServiceModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        row.status = new_status.value
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def soft_delete(self, request_id: int) -> bool:
        q = select(RequestServiceModel).where(
            RequestServiceModel.id == request_id,
            RequestServiceModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        row.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True
