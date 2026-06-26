"""Interfaces (ABC) des repositories Logistic."""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from app.modules.logistique.domain.entites import ShippingRate, ShippingZone
from app.shared.schemas.pagination import PaginationParams


class ShippingZoneRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[ShippingZone]: ...

    @abstractmethod
    async def get_by_id(self, id_zone: int) -> ShippingZone | None: ...

    @abstractmethod
    async def create(
        self, nom: str, description: str | None, est_actif: bool
    ) -> ShippingZone: ...

    @abstractmethod
    async def update(
        self, id_zone: int, nom: str | None, description: str | None, est_actif: bool | None
    ) -> ShippingZone | None: ...

    @abstractmethod
    async def soft_delete(self, id_zone: int) -> bool: ...


class ShippingRateRepository(ABC):
    @abstractmethod
    async def list_by_zone(
        self, id_zone: int, min_amount: Decimal | None = None
    ) -> list[ShippingRate]: ...

    @abstractmethod
    async def get_by_id(self, rate_id: int) -> ShippingRate | None: ...

    @abstractmethod
    async def create(
        self,
        id_zone: int,
        nom: str,
        poids_min: Decimal,
        poids_max: Decimal | None,
        montant_min_commande: Decimal,
        tarif: Decimal,
        livraison_gratuite: bool,
        jours_livraison_min: int,
        jours_livraison_max: int,
        est_actif: bool,
    ) -> ShippingRate: ...

    @abstractmethod
    async def update(
        self,
        rate_id: int,
        nom: str | None,
        poids_min: Decimal | None,
        poids_max: Decimal | None,
        montant_min_commande: Decimal | None,
        tarif: Decimal | None,
        livraison_gratuite: bool | None,
        jours_livraison_min: int | None,
        jours_livraison_max: int | None,
        est_actif: bool | None,
    ) -> ShippingRate | None: ...

    @abstractmethod
    async def soft_delete(self, rate_id: int) -> bool: ...
