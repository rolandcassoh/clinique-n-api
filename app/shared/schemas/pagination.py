from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


class Page(BaseModel, Generic[T]):
    """Réponse paginée générique."""

    model_config = ConfigDict(from_attributes=True)

    data: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int

    @classmethod
    def create(cls, data: list[T], total: int, params: PaginationParams) -> "Page[T]":
        import math

        return cls(
            data=data,
            total=total,
            page=params.page,
            per_page=params.per_page,
            total_pages=math.ceil(total / params.per_page) if total > 0 else 0,
        )
