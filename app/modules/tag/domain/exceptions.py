from app.shared.exceptions.domain import EntityNotFoundError, ConflictError

__all__ = ["TagNotFoundError", "TagSlugConflictError"]


class TagNotFoundError(EntityNotFoundError):
    def __init__(self, identifier: str | int) -> None:
        super().__init__("Tag", identifier)


class TagSlugConflictError(ConflictError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"Tag slug '{slug}' already exists.")
