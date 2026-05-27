"""Use cases — module subscription."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.modules.subscription.domain.entities import Subscription, SubscriptionPlan
from app.modules.subscription.domain.exceptions import (
    ActiveSubscriptionExistsError,
    CannotRenewCancelledError,
    PlanLimitationNotFoundError,
    SubscriptionNotFoundError,
    SubscriptionPlanNotFoundError,
)
from app.modules.subscription.domain.repositories import (
    AbstractSubscriptionPlanRepository,
    AbstractSubscriptionRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams


# ── Plans ─────────────────────────────────────────────────────────────────────

class ListPlansUseCase:
    def __init__(self, repo: AbstractSubscriptionPlanRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[SubscriptionPlan]:
        return await self._repo.list_active()


class GetPlanBySlugUseCase:
    def __init__(self, repo: AbstractSubscriptionPlanRepository) -> None:
        self._repo = repo

    async def execute(self, slug: str) -> SubscriptionPlan:
        plan = await self._repo.get_by_slug(slug)
        if plan is None:
            raise SubscriptionPlanNotFoundError(slug)
        return plan


class CreatePlanUseCase:
    def __init__(self, repo: AbstractSubscriptionPlanRepository) -> None:
        self._repo = repo

    async def execute(
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
        return await self._repo.create(
            name=name, slug=slug, price=price, billing_period=billing_period,
            description=description, trial_days=trial_days,
            is_featured=is_featured, sort_order=sort_order,
        )


class UpdatePlanUseCase:
    def __init__(self, repo: AbstractSubscriptionPlanRepository) -> None:
        self._repo = repo

    async def execute(self, plan_id: int, **kwargs: Any) -> SubscriptionPlan:
        updated = await self._repo.update(plan_id, **kwargs)
        if updated is None:
            raise SubscriptionPlanNotFoundError(plan_id)
        return updated


class UpsertPlanLimitationUseCase:
    def __init__(self, repo: AbstractSubscriptionPlanRepository) -> None:
        self._repo = repo

    async def execute(self, plan_id: int, feature: str, value: str):
        plan = await self._repo.get_by_id(plan_id)
        if plan is None:
            raise SubscriptionPlanNotFoundError(plan_id)
        return await self._repo.upsert_limitation(plan_id, feature, value)


class DeletePlanLimitationUseCase:
    def __init__(self, repo: AbstractSubscriptionPlanRepository) -> None:
        self._repo = repo

    async def execute(self, plan_id: int, feature: str) -> None:
        deleted = await self._repo.delete_limitation(plan_id, feature)
        if not deleted:
            raise PlanLimitationNotFoundError(plan_id, feature)


# ── Subscriptions ─────────────────────────────────────────────────────────────

class SubscribeUseCase:
    """
    Règles :
    1. Vérifier que la clinique n'a pas déjà un abonnement actif/trial
    2. Si trial_days > 0 → status='trial', ends_at = now + trial_days jours
    3. Sinon → status='active', ends_at calculé selon billing_period (30j ou 365j)
    """
    def __init__(
        self,
        plan_repo: AbstractSubscriptionPlanRepository,
        sub_repo: AbstractSubscriptionRepository,
    ) -> None:
        self._plan_repo = plan_repo
        self._sub_repo = sub_repo

    async def execute(self, clinic_id: int, plan_id: int) -> Subscription:
        # 1. Vérifier pas de sub active
        existing = await self._sub_repo.get_active_for_clinic(clinic_id)
        if existing is not None:
            raise ActiveSubscriptionExistsError(clinic_id)

        # 2. Charger le plan
        plan = await self._plan_repo.get_by_id(plan_id)
        if plan is None:
            raise SubscriptionPlanNotFoundError(plan_id)

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if plan.trial_days > 0:
            sub_status = "trial"
            ends_at = now + timedelta(days=plan.trial_days)
        else:
            sub_status = "active"
            ends_at = now + timedelta(days=plan.period_days())

        return await self._sub_repo.create(
            clinic_id=clinic_id,
            plan_id=plan_id,
            status=sub_status,
            starts_at=now,
            ends_at=ends_at,
        )


class GetCurrentSubscriptionUseCase:
    def __init__(self, repo: AbstractSubscriptionRepository) -> None:
        self._repo = repo

    async def execute(self, clinic_id: int) -> Subscription:
        sub = await self._repo.get_active_for_clinic(clinic_id)
        if sub is None:
            raise SubscriptionNotFoundError(0)
        return sub


class CancelSubscriptionUseCase:
    def __init__(self, repo: AbstractSubscriptionRepository) -> None:
        self._repo = repo

    async def execute(self, subscription_id: int) -> Subscription:
        sub = await self._repo.get_by_id(subscription_id)
        if sub is None:
            raise SubscriptionNotFoundError(subscription_id)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sub.cancel(now)
        updated = await self._repo.update(
            subscription_id,
            auto_renew=False,
            status="cancelled",
            cancelled_at=now,
        )
        if updated is None:
            raise SubscriptionNotFoundError(subscription_id)
        return updated


class RenewSubscriptionUseCase:
    """
    Règles :
    1. Vérifier que l'abonnement est actif ou expiré (pas cancelled)
    2. Calculer nouvelle ends_at = max(now, ancien ends_at) + période
    3. status = 'active', auto_renew = true
    """
    def __init__(
        self,
        plan_repo: AbstractSubscriptionPlanRepository,
        sub_repo: AbstractSubscriptionRepository,
    ) -> None:
        self._plan_repo = plan_repo
        self._sub_repo = sub_repo

    async def execute(
        self,
        subscription_id: int,
        plan_id: Optional[int] = None,
    ) -> Subscription:
        sub = await self._sub_repo.get_by_id(subscription_id)
        if sub is None:
            raise SubscriptionNotFoundError(subscription_id)

        if sub.status == "cancelled":
            raise CannotRenewCancelledError(subscription_id)

        # Optionnellement changer de plan
        target_plan_id = plan_id if plan_id is not None else sub.plan_id
        plan = await self._plan_repo.get_by_id(target_plan_id)
        if plan is None:
            raise SubscriptionPlanNotFoundError(target_plan_id)

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        new_ends_at = max(now, sub.ends_at) + timedelta(days=plan.period_days())

        updated = await self._sub_repo.update(
            subscription_id,
            plan_id=target_plan_id,
            status="active",
            ends_at=new_ends_at,
            auto_renew=True,
        )
        if updated is None:
            raise SubscriptionNotFoundError(subscription_id)
        return updated


class ListAdminSubscriptionsUseCase:
    def __init__(self, repo: AbstractSubscriptionRepository) -> None:
        self._repo = repo

    async def execute(self, params: PaginationParams) -> Page[Subscription]:
        data, total = await self._repo.list_paginated(params)
        return Page.create(data, total, params)


class GetAdminSubscriptionUseCase:
    def __init__(self, repo: AbstractSubscriptionRepository) -> None:
        self._repo = repo

    async def execute(self, subscription_id: int) -> Subscription:
        sub = await self._repo.get_by_id(subscription_id)
        if sub is None:
            raise SubscriptionNotFoundError(subscription_id)
        return sub


class ForceSubscriptionStatusUseCase:
    def __init__(self, repo: AbstractSubscriptionRepository) -> None:
        self._repo = repo

    async def execute(self, subscription_id: int, new_status: str) -> Subscription:
        updated = await self._repo.update(subscription_id, status=new_status)
        if updated is None:
            raise SubscriptionNotFoundError(subscription_id)
        return updated
