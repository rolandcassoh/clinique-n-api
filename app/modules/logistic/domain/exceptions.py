"""Exceptions métier du module Logistic."""
from app.shared.exceptions.domain import EntityNotFoundError


class ShippingZoneNotFoundError(EntityNotFoundError):
    def __init__(self, zone_id: int) -> None:
        super().__init__("ShippingZone", zone_id)


class ShippingRateNotFoundError(EntityNotFoundError):
    def __init__(self, rate_id: int) -> None:
        super().__init__("ShippingRate", rate_id)


class NoApplicableShippingRateError(Exception):
    def __init__(self, zone_id: int, amount: float) -> None:
        super().__init__(
            f"No applicable shipping rate found for zone {zone_id} and amount {amount}."
        )
        self.zone_id = zone_id
        self.amount = amount
