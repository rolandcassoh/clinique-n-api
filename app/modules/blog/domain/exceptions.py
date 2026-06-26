"""Exceptions métier du module blog."""
from app.shared.exceptions.domain import ConflictError, EntityNotFoundError


class BlogPostNotFoundError(EntityNotFoundError):
    def __init__(self, identifier: str | int) -> None:
        super().__init__("BlogPost", identifier)


class BlogCategoryNotFoundError(EntityNotFoundError):
    def __init__(self, identifier: str | int) -> None:
        super().__init__("BlogCategory", identifier)


class SlugAlreadyExistsError(ConflictError):
    def __init__(self, identifiant_url: str) -> None:
        super().__init__(f"Un article de blog avec le identifiant_url '{identifiant_url}' existe déjà.")
