"""Exceptions métier du module slider."""
from app.shared.exceptions.domain import EntityNotFoundError


class SliderNotFoundError(EntityNotFoundError):
    def __init__(self, identifier: str | int) -> None:
        super().__init__("Slider", identifier)
