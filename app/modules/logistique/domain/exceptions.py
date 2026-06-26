"""Exceptions métier du module Logistic."""
from app.shared.exceptions.domain import EntityNotFoundError


class ShippingZoneNotFoundError(EntityNotFoundError):
    def __init__(self, id_zone: int) -> None:
        super().__init__("ShippingZone", id_zone)


class ShippingRateNotFoundError(EntityNotFoundError):
    def __init__(self, rate_id: int) -> None:
        super().__init__("ShippingRate", rate_id)


class NoApplicableShippingRateError(Exception):
    def __init__(self, id_zone: int, montant: float) -> None:
        super().__init__(
            f"Aucun tarif de livraison applicable trouvé pour la zone {id_zone} et le montant {montant}."
        )
        self.id_zone = id_zone
        self.montant = montant
