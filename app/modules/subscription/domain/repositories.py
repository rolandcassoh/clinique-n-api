from abc import ABC, abstractmethod
from typing import Optional

from app.modules.subscription.domain.entities import (
    PlanLimitation,
    Subscription,
    SubscriptionPlan,
)
from app.shared.schemas.pagination import PaginationParams


class AbstractSubscriptionPlanRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[SubscriptionPlan]:
        ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[SubscriptionPlan]:
        ...

    @abstractmethod
    async def get_by_id(self, plan_id: int) -> Optional[SubscriptionPlan]:
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def update(self, plan_id: int, **kwargs) -> Optional[SubscriptionPlan]:
        ...

    @abstractmethod
    async def upsert_limitation(
        self, plan_id: int, feature: str, value: str
    ) -> PlanLimitation:
        ...

    @abstractmethod
    async def delete_limitation(self, plan_id: int, feature: str) -> bool:
        ...


class AbstractSubscriptionRepository(ABC):
    @abstractmethod
    async def list_paginated(
        self, params: PaginationParams
    ) -> tuple[list[Subscription], int]:
        ...

    @abstractmethod
    async def get_by_id(self, subscription_id: int) -> Optional[Subscription]:
        ...

    @abstractmethod
    async def get_active_for_clinic(self, clinic_id: int) -> Optional[Subscription]:
        ...

    @abstractmethod
    async def create(
        self,
        clinic_id: int,
        plan_id: int,
        status: str,
        starts_at,
        ends_at,
        auto_renew: bool = True,
    ) -> Subscription:
        ...

    @abstractmethod
    async def update(self, subscription_id: int, **kwargs) -> Optional[Subscription]:
        ...
