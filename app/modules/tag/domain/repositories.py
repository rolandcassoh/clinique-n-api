from abc import ABC, abstractmethod

from app.modules.tag.domain.entities import Tag


class AbstractTagRepository(ABC):
    @abstractmethod
    async def list(self, type_filter: str | None = None, search: str | None = None) -> list[Tag]:
        ...

    @abstractmethod
    async def get_by_id(self, tag_id: int) -> Tag | None:
        ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Tag | None:
        ...

    @abstractmethod
    async def create(self, name: str, slug: str, type: str | None) -> Tag:
        ...

    @abstractmethod
    async def update(self, tag_id: int, name: str, slug: str, type: str | None) -> Tag | None:
        ...

    @abstractmethod
    async def soft_delete(self, tag_id: int) -> bool:
        ...
