"""Exceptions métier du module page."""
from app.shared.exceptions.domain import ConflictError, EntityNotFoundError


class PageNotFoundError(EntityNotFoundError):
    def __init__(self, identifier: str | int) -> None:
        super().__init__("Page", identifier)


class PageSlugAlreadyExistsError(ConflictError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"A page with slug '{slug}' already exists.")
