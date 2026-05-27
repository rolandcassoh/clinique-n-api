"""Interfaces (ABC) des repositories Logistic."""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from app.modules.logistic.domain.entities import ShippingRate, ShippingZone
from app.shared.schemas.pagination import PaginationParams


class ShippingZoneRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[ShippingZone]: ...

    @abstractmethod
    async def get_by_id(self, zone_id: int) -> ShippingZone | None: ...

    @abstractmethod
    async def create(
        self, name: str, description: str | None, is_active: bool
    ) -> ShippingZone: ...

    @abstractmethod
    async def update(
        self, zone_id: int, name: str | None, description: str | None, is_active: bool | None
    ) -> ShippingZone | None: ...

    @abstractmethod
    async def soft_delete(self, zone_id: int) -> bool: ...


class ShippingRateRepository(ABC):
    @abstractmethod
    async def list_by_zone(
        self, zone_id: int, min_amount: Decimal | None = None
    ) -> list[ShippingRate]: ...

    @abstractmethod
    async def get_by_id(self, rate_id: int) -> ShippingRate | None: ...

    @abstractmethod
    async def create(
        self,
        zone_id: int,
        name: str,
        min_weight: Decimal,
        max_weight: Decimal | None,
        min_order_amount: Decimal,
        rate: Decimal,
        is_free_shipping: bool,
        estimated_days_min: int,
        estimated_days_max: int,
        is_active: bool,
    ) -> ShippingRate: ...

    @abstractmethod
    async def update(
        self,
        rate_id: int,
        name: str | None,
        min_weight: Decimal | None,
        max_weight: Decimal | None,
        min_order_amount: Decimal | None,
        rate: Decimal | None,
        is_free_shipping: bool | None,
        estimated_days_min: int | None,
        estimated_days_max: int | None,
        is_active: bool | None,
    ) -> ShippingRate | None: ...

    @abstractmethod
    async def soft_delete(self, rate_id: int) -> bool: ...
