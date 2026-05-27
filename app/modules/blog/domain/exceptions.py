"""Exceptions métier du module blog."""
from app.shared.exceptions.domain import ConflictError, EntityNotFoundError


class BlogPostNotFoundError(EntityNotFoundError):
    def __init__(self, identifier: str | int) -> None:
        super().__init__("BlogPost", identifier)


class BlogCategoryNotFoundError(EntityNotFoundError):
    def __init__(self, identifier: str | int) -> None:
        super().__init__("BlogCategory", identifier)


class SlugAlreadyExistsError(ConflictError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"A blog post with slug '{slug}' already exists.")
