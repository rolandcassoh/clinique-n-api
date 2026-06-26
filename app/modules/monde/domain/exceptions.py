"""Exceptions métier du module world."""
from app.shared.exceptions.domain import EntityNotFoundError


class CountryNotFoundError(EntityNotFoundError):
    def __init__(self, id_pays: int) -> None:
        super().__init__("Country", id_pays)


class StateNotFoundError(EntityNotFoundError):
    def __init__(self, id_region: int) -> None:
        super().__init__("State", id_region)


class CityNotFoundError(EntityNotFoundError):
    def __init__(self, id_ville: int) -> None:
        super().__init__("City", id_ville)
