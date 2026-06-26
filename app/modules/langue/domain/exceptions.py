"""Exceptions métier du module langue (language)."""
from app.shared.exceptions.domain import EntityNotFoundError, ConflictError


class LanguageNotFoundError(EntityNotFoundError):
    def __init__(self, identifier: str | int) -> None:
        super().__init__("Language", identifier)


class LanguageCodeConflictError(ConflictError):
    def __init__(self, code: str) -> None:
        super().__init__(f"Le code langue '{code}' existe déjà.")
