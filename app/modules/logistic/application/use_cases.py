"""Use Cases du module Logistic."""
from __future__ import annotations

from decimal import Decimal

from app.modules.logistic.domain.entities import (
    ShippingCalculationResult,
    ShippingRate,
    ShippingZone,
)
from app.modules.logistic.domain.exceptions import (
    NoApplicableShippingRateError,
    ShippingRateNotFoundError,
    ShippingZoneNotFoundError,
)
from app.modules.logistic.domain.repositories import ShippingRateRepository, ShippingZoneRepository


class ListActiveZonesUseCase:
    def __init__(self, repo: ShippingZoneRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[ShippingZone]:
        return await self._repo.list_active()


class CreateZoneUseCase:
    def __init__(self, repo: ShippingZoneRepository) -> None:
        self._repo = repo

    async def execute(
        self, name: str, description: str | None = None, is_active: bool = True
    ) -> ShippingZone:
        return await self._repo.create(name=name, description=description, is_active=is_active)


class UpdateZoneUseCase:
    def __init__(self, repo: ShippingZoneRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        zone_id: int,
        name: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> ShippingZone:
        zone = await self._repo.update(
            zone_id=zone_id, name=name, description=description, is_active=is_active
        )
        if zone is None:
            raise ShippingZoneNotFoundError(zone_id)
        return zone


class DeleteZoneUseCase:
    def __init__(self, repo: ShippingZoneRepository) -> None:
        self._repo = repo

    async def execute(self, zone_id: int) -> None:
        deleted = await self._repo.soft_delete(zone_id)
        if not deleted:
            raise ShippingZoneNotFoundError(zone_id)


class ListRatesUseCase:
    def __init__(self, repo: ShippingRateRepository) -> None:
        self._repo = repo

    async def execute(
        self, zone_id: int, amount: Decimal | None = None
    ) -> list[ShippingRate]:
        return await self._repo.list_by_zone(zone_id, min_amount=amount)


class CreateRateUseCase:
    def __init__(self, repo: ShippingRateRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        zone_id: int,
        name: str,
        rate: Decimal,
        min_weight: Decimal = Decimal("0"),
        max_weight: Decimal | None = None,
        min_order_amount: Decimal = Decimal("0"),
        is_free_shipping: bool = False,
        estimated_days_min: int = 1,
        estimated_days_max: int = 3,
        is_active: bool = True,
    ) -> ShippingRate:
        return await self._repo.create(
            zone_id=zone_id, name=name, min_weight=min_weight, max_weight=max_weight,
            min_order_amount=min_order_amount, rate=rate, is_free_shipping=is_free_shipping,
            estimated_days_min=estimated_days_min, estimated_days_max=estimated_days_max,
            is_active=is_active,
        )


class UpdateRateUseCase:
    def __init__(self, repo: ShippingRateRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        rate_id: int,
        name: str | None = None,
        min_weight: Decimal | None = None,
        max_weight: Decimal | None = None,
        min_order_amount: Decimal | None = None,
        rate: Decimal | None = None,
        is_free_shipping: bool | None = None,
        estimated_days_min: int | None = None,
        estimated_days_max: int | None = None,
        is_active: bool | None = None,
    ) -> ShippingRate:
        result = await self._repo.update(
            rate_id=rate_id, name=name, min_weight=min_weight, max_weight=max_weight,
            min_order_amount=min_order_amount, rate=rate, is_free_shipping=is_free_shipping,
            estimated_days_min=estimated_days_min, estimated_days_max=estimated_days_max,
            is_active=is_active,
        )
        if result is None:
            raise ShippingRateNotFoundError(rate_id)
        return result


class DeleteRateUseCase:
    def __init__(self, repo: ShippingRateRepository) -> None:
        self._repo = repo

    async def execute(self, rate_id: int) -> None:
        deleted = await self._repo.soft_delete(rate_id)
        if not deleted:
            raise ShippingRateNotFoundError(rate_id)


class CalculateShippingUseCase:
    """
    Algorithme de calcul :
    1. Filtrer les tarifs actifs de la zone
    2. Garder ceux où min_order_amount <= amount
    3. Si is_free_shipping=true → retourner {rate: 0, estimated_days: ...}
    4. Sinon → retourner le tarif le moins cher applicable
    """

    def __init__(self, repo: ShippingRateRepository) -> None:
        self._repo = repo

    async def execute(self, zone_id: int, amount: Decimal) -> ShippingCalculationResult:
        rates = await self._repo.list_by_zone(zone_id, min_amount=amount)

        if not rates:
            raise NoApplicableShippingRateError(zone_id, float(amount))

        # Priorité au tarif gratuit
        for r in rates:
            if r.is_free_shipping:
                return ShippingCalculationResult(
                    rate=Decimal("0"),
                    estimated_days_min=r.estimated_days_min,
                    estimated_days_max=r.estimated_days_max,
                    rate_name=r.name,
                    is_free_shipping=True,
                )

        # Sinon, le tarif le moins cher
        cheapest = min(rates, key=lambda r: r.rate)
        return ShippingCalculationResult(
            rate=cheapest.rate,
            estimated_days_min=cheapest.estimated_days_min,
            estimated_days_max=cheapest.estimated_days_max,
            rate_name=cheapest.name,
            is_free_shipping=False,
        )
