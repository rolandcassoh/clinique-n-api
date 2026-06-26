from abc import ABC, abstractmethod
from typing import Optional

from app.modules.abonnement.domain.entites import (
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
    async def get_by_slug(self, identifiant_url: str) -> Optional[SubscriptionPlan]:
        ...

    @abstractmethod
    async def get_by_id(self, id_plan: int) -> Optional[SubscriptionPlan]:
        ...

    @abstractmethod
    async def create(
        self,
        nom: str,
        identifiant_url: str,
        prix: float,
        periode_facturation: str = "monthly",
        description: Optional[str] = None,
        jours_essai: int = 0,
        est_mis_en_avant: bool = False,
        ordre_affichage: int = 0,
    ) -> SubscriptionPlan:
        ...

    @abstractmethod
    async def update(self, id_plan: int, **kwargs) -> Optional[SubscriptionPlan]:
        ...

    @abstractmethod
    async def upsert_limitation(
        self, id_plan: int, fonctionnalite: str, valeur: str
    ) -> PlanLimitation:
        ...

    @abstractmethod
    async def delete_limitation(self, id_plan: int, fonctionnalite: str) -> bool:
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
    async def get_active_for_clinic(self, id_clinique: int) -> Optional[Subscription]:
        ...

    @abstractmethod
    async def create(
        self,
        id_clinique: int,
        id_plan: int,
        statut: str,
        debut_le,
        fin_le,
        renouvellement_auto: bool = True,
    ) -> Subscription:
        ...

    @abstractmethod
    async def update(self, subscription_id: int, **kwargs) -> Optional[Subscription]:
        ...
