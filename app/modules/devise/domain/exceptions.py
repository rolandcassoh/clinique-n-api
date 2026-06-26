"""Exceptions métier du module devise (devise)."""
from app.shared.exceptions.domain import EntityNotFoundError, ConflictError

__all__ = ["CurrencyNotFoundError", "CurrencyCodeConflictError"]


class CurrencyNotFoundError(EntityNotFoundError):
    def __init__(self, identifier: str | int) -> None:
        super().__init__("Currency", identifier)


class CurrencyCodeConflictError(ConflictError):
    def __init__(self, code: str) -> None:
        super().__init__(f"Le code devise '{code}' existe déjà.")
