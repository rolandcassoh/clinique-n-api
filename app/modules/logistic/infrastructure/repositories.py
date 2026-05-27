"""Implémentation SQLAlchemy async des repositories Logistic."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.logistic.domain.entities import ShippingRate, ShippingZone
from app.modules.logistic.domain.repositories import ShippingRateRepository, ShippingZoneRepository
from app.modules.logistic.infrastructure.models import ShippingRateModel, ShippingZoneModel


def _zone_to_entity(m: ShippingZoneModel) -> ShippingZone:
    return ShippingZone(
        id=m.id, name=m.name, description=m.description, is_active=m.is_active,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _rate_to_entity(m: ShippingRateModel) -> ShippingRate:
    return ShippingRate(
        id=m.id, zone_id=m.zone_id, name=m.name,
        min_weight=m.min_weight, max_weight=m.max_weight,
        min_order_amount=m.min_order_amount, rate=m.rate,
        is_free_shipping=m.is_free_shipping,
        estimated_days_min=m.estimated_days_min, estimated_days_max=m.estimated_days_max,
        is_active=m.is_active, created_at=m.created_at, updated_at=m.updated_at,
    )


class SQLAlchemyShippingZoneRepository(ShippingZoneRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[ShippingZone]:
        q = select(ShippingZoneModel).where(
            ShippingZoneModel.deleted_at.is_(None),
            ShippingZoneModel.is_active.is_(True),
        ).order_by(ShippingZoneModel.id)
        rows = (await self._session.execute(q)).scalars().all()
        return [_zone_to_entity(r) for r in rows]

    async def get_by_id(self, zone_id: int) -> ShippingZone | None:
        q = select(ShippingZoneModel).where(
            ShippingZoneModel.id == zone_id,
            ShippingZoneModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _zone_to_entity(row) if row else None

    async def create(self, name: str, description: str | None, is_active: bool) -> ShippingZone:
        m = ShippingZoneModel(name=name, description=description, is_active=is_active)
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _zone_to_entity(m)

    async def update(
        self, zone_id: int, name: str | None, description: str | None, is_active: bool | None
    ) -> ShippingZone | None:
        q = select(ShippingZoneModel).where(
            ShippingZoneModel.id == zone_id,
            ShippingZoneModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        if name is not None:
            row.name = name
        if description is not None:
            row.description = description
        if is_active is not None:
            row.is_active = is_active
        await self._session.flush()
        await self._session.refresh(row)
        return _zone_to_entity(row)

    async def soft_delete(self, zone_id: int) -> bool:
        q = select(ShippingZoneModel).where(
            ShippingZoneModel.id == zone_id,
            ShippingZoneModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        row.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True


class SQLAlchemyShippingRateRepository(ShippingRateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_zone(
        self, zone_id: int, min_amount: Decimal | None = None
    ) -> list[ShippingRate]:
        q = select(ShippingRateModel).where(
            ShippingRateModel.zone_id == zone_id,
            ShippingRateModel.deleted_at.is_(None),
            ShippingRateModel.is_active.is_(True),
        )
        if min_amount is not None:
            q = q.where(ShippingRateModel.min_order_amount <= min_amount)
        rows = (await self._session.execute(q)).scalars().all()
        return [_rate_to_entity(r) for r in rows]

    async def get_by_id(self, rate_id: int) -> ShippingRate | None:
        q = select(ShippingRateModel).where(
            ShippingRateModel.id == rate_id,
            ShippingRateModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _rate_to_entity(row) if row else None

    async def create(
        self, zone_id: int, name: str, min_weight: Decimal, max_weight: Decimal | None,
        min_order_amount: Decimal, rate: Decimal, is_free_shipping: bool,
        estimated_days_min: int, estimated_days_max: int, is_active: bool,
    ) -> ShippingRate:
        m = ShippingRateModel(
            zone_id=zone_id, name=name, min_weight=min_weight, max_weight=max_weight,
            min_order_amount=min_order_amount, rate=rate, is_free_shipping=is_free_shipping,
            estimated_days_min=estimated_days_min, estimated_days_max=estimated_days_max,
            is_active=is_active,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _rate_to_entity(m)

    async def update(
        self, rate_id: int, name: str | None, min_weight: Decimal | None,
        max_weight: Decimal | None, min_order_amount: Decimal | None, rate: Decimal | None,
        is_free_shipping: bool | None, estimated_days_min: int | None,
        estimated_days_max: int | None, is_active: bool | None,
    ) -> ShippingRate | None:
        q = select(ShippingRateModel).where(
            ShippingRateModel.id == rate_id,
            ShippingRateModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        for attr, val in [
            ("name", name), ("min_weight", min_weight), ("max_weight", max_weight),
            ("min_order_amount", min_order_amount), ("rate", rate),
            ("is_free_shipping", is_free_shipping), ("estimated_days_min", estimated_days_min),
            ("estimated_days_max", estimated_days_max), ("is_active", is_active),
        ]:
            if val is not None:
                setattr(row, attr, val)
        await self._session.flush()
        await self._session.refresh(row)
        return _rate_to_entity(row)

    async def soft_delete(self, rate_id: int) -> bool:
        q = select(ShippingRateModel).where(
            ShippingRateModel.id == rate_id,
            ShippingRateModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        row.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True
