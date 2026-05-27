"""SQLAlchemy repositories — module subscription."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.subscription.domain.entities import (
    PlanLimitation,
    Subscription,
    SubscriptionPlan,
)
from app.modules.subscription.domain.repositories import (
    AbstractSubscriptionPlanRepository,
    AbstractSubscriptionRepository,
)
from app.modules.subscription.infrastructure.models import (
    PlanLimitationModel,
    SubscriptionModel,
    SubscriptionPlanModel,
)
from app.shared.schemas.pagination import PaginationParams


# ── Mappers ───────────────────────────────────────────────────────────────────

def _to_limitation(m: PlanLimitationModel) -> PlanLimitation:
    return PlanLimitation(
        id=m.id, plan_id=m.plan_id, feature=m.feature, value=m.value,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _to_plan(m: SubscriptionPlanModel, limitations: list[PlanLimitation] | None = None) -> SubscriptionPlan:
    return SubscriptionPlan(
        id=m.id, name=m.name, slug=m.slug, description=m.description,
        price=m.price, billing_period=m.billing_period, trial_days=m.trial_days,
        is_active=m.is_active, is_featured=m.is_featured, sort_order=m.sort_order,
        created_at=m.created_at, updated_at=m.updated_at, deleted_at=m.deleted_at,
        limitations=limitations or [],
    )


def _to_subscription(m: SubscriptionModel) -> Subscription:
    return Subscription(
        id=m.id, clinic_id=m.clinic_id, plan_id=m.plan_id,
        status=m.status, starts_at=m.starts_at, ends_at=m.ends_at,
        auto_renew=m.auto_renew, cancelled_at=m.cancelled_at,
        created_at=m.created_at, updated_at=m.updated_at, deleted_at=m.deleted_at,
    )


# ── SubscriptionPlanRepository ────────────────────────────────────────────────

class SQLSubscriptionPlanRepository(AbstractSubscriptionPlanRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _load_limitations(self, plan_id: int) -> list[PlanLimitation]:
        stmt = select(PlanLimitationModel).where(PlanLimitationModel.plan_id == plan_id)
        result = await self._session.execute(stmt)
        return [_to_limitation(m) for m in result.scalars().all()]

    async def list_active(self) -> list[SubscriptionPlan]:
        stmt = (
            select(SubscriptionPlanModel)
            .where(
                SubscriptionPlanModel.is_active.is_(True),
                SubscriptionPlanModel.deleted_at.is_(None),
            )
            .order_by(SubscriptionPlanModel.sort_order)
        )
        result = await self._session.execute(stmt)
        plans = []
        for m in result.scalars().all():
            limitations = await self._load_limitations(m.id)
            plans.append(_to_plan(m, limitations))
        return plans

    async def get_by_slug(self, slug: str) -> Optional[SubscriptionPlan]:
        stmt = select(SubscriptionPlanModel).where(
            SubscriptionPlanModel.slug == slug,
            SubscriptionPlanModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        if m is None:
            return None
        limitations = await self._load_limitations(m.id)
        return _to_plan(m, limitations)

    async def get_by_id(self, plan_id: int) -> Optional[SubscriptionPlan]:
        stmt = select(SubscriptionPlanModel).where(
            SubscriptionPlanModel.id == plan_id,
            SubscriptionPlanModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        if m is None:
            return None
        limitations = await self._load_limitations(m.id)
        return _to_plan(m, limitations)

    async def create(
        self,
        name: str,
        slug: str,
        price: float,
        billing_period: str = "monthly",
        description: Optional[str] = None,
        trial_days: int = 0,
        is_featured: bool = False,
        sort_order: int = 0,
    ) -> SubscriptionPlan:
        m = SubscriptionPlanModel(
            name=name, slug=slug, price=Decimal(str(price)),
            billing_period=billing_period, description=description,
            trial_days=trial_days, is_featured=is_featured, sort_order=sort_order,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_plan(m)

    async def update(self, plan_id: int, **kwargs) -> Optional[SubscriptionPlan]:
        stmt = (
            update(SubscriptionPlanModel)
            .where(
                SubscriptionPlanModel.id == plan_id,
                SubscriptionPlanModel.deleted_at.is_(None),
            )
            .values(**kwargs)
            .returning(SubscriptionPlanModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        if m is None:
            return None
        limitations = await self._load_limitations(plan_id)
        return _to_plan(m, limitations)

    async def upsert_limitation(
        self, plan_id: int, feature: str, value: str
    ) -> PlanLimitation:
        # Cherche une existante
        stmt = select(PlanLimitationModel).where(
            PlanLimitationModel.plan_id == plan_id,
            PlanLimitationModel.feature == feature,
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        if m is not None:
            m.value = value
            await self._session.flush()
            await self._session.refresh(m)
        else:
            m = PlanLimitationModel(plan_id=plan_id, feature=feature, value=value)
            self._session.add(m)
            await self._session.flush()
            await self._session.refresh(m)
        return _to_limitation(m)

    async def delete_limitation(self, plan_id: int, feature: str) -> bool:
        stmt = select(PlanLimitationModel).where(
            PlanLimitationModel.plan_id == plan_id,
            PlanLimitationModel.feature == feature,
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        if m is None:
            return False
        await self._session.delete(m)
        await self._session.flush()
        return True


# ── SubscriptionRepository ────────────────────────────────────────────────────

class SQLSubscriptionRepository(AbstractSubscriptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_paginated(
        self, params: PaginationParams
    ) -> tuple[list[Subscription], int]:
        base = select(SubscriptionModel).where(SubscriptionModel.deleted_at.is_(None))
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        data_stmt = base.order_by(SubscriptionModel.created_at.desc()).offset(params.offset).limit(params.per_page)
        result = await self._session.execute(data_stmt)
        return [_to_subscription(m) for m in result.scalars().all()], total

    async def get_by_id(self, subscription_id: int) -> Optional[Subscription]:
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.id == subscription_id,
            SubscriptionModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_subscription(m) if m else None

    async def get_active_for_clinic(self, clinic_id: int) -> Optional[Subscription]:
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.clinic_id == clinic_id,
            SubscriptionModel.deleted_at.is_(None),
            or_(
                SubscriptionModel.status == "active",
                SubscriptionModel.status == "trial",
            ),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_subscription(m) if m else None

    async def create(
        self,
        clinic_id: int,
        plan_id: int,
        status: str,
        starts_at,
        ends_at,
        auto_renew: bool = True,
    ) -> Subscription:
        m = SubscriptionModel(
            clinic_id=clinic_id, plan_id=plan_id, status=status,
            starts_at=starts_at, ends_at=ends_at, auto_renew=auto_renew,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_subscription(m)

    async def update(self, subscription_id: int, **kwargs) -> Optional[Subscription]:
        stmt = (
            update(SubscriptionModel)
            .where(
                SubscriptionModel.id == subscription_id,
                SubscriptionModel.deleted_at.is_(None),
            )
            .values(**kwargs)
            .returning(SubscriptionModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_subscription(m) if m else None
