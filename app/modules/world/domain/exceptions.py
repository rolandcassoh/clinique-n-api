"""Exceptions métier du module world."""
from app.shared.exceptions.domain import EntityNotFoundError


class CountryNotFoundError(EntityNotFoundError):
    def __init__(self, country_id: int) -> None:
        super().__init__("Country", country_id)


class StateNotFoundError(EntityNotFoundError):
    def __init__(self, state_id: int) -> None:
        super().__init__("State", state_id)


class CityNotFoundError(EntityNotFoundError):
    def __init__(self, city_id: int) -> None:
        super().__init__("City", city_id)
