"""Exceptions métier du module tag."""
from app.shared.exceptions.domain import EntityNotFoundError, ConflictError

__all__ = ["TagNotFoundError", "TagSlugConflictError"]


class TagNotFoundError(EntityNotFoundError):
    def __init__(self, identifier: str | int) -> None:
        super().__init__("Tag", identifier)


class TagSlugConflictError(ConflictError):
    def __init__(self, identifiant_url: str) -> None:
        super().__init__(f"Le identifiant_url de tag '{identifiant_url}' existe déjà.")
