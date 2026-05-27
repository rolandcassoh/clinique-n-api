from app.modules.tag.domain.entities import Tag
from app.modules.tag.domain.exceptions import TagNotFoundError, TagSlugConflictError
from app.modules.tag.domain.repositories import AbstractTagRepository


class TagUseCases:
    def __init__(self, repo: AbstractTagRepository) -> None:
        self._repo = repo

    async def list_tags(self, type_filter: str | None = None, search: str | None = None) -> list[Tag]:
        return await self._repo.list(type_filter=type_filter, search=search)

    async def get_tag(self, tag_id: int) -> Tag:
        tag = await self._repo.get_by_id(tag_id)
        if tag is None:
            raise TagNotFoundError(tag_id)
        return tag

    async def create_tag(self, name: str, slug: str, type: str | None) -> Tag:
        existing = await self._repo.get_by_slug(slug)
        if existing is not None:
            raise TagSlugConflictError(slug)
        return await self._repo.create(name=name, slug=slug, type=type)

    async def update_tag(self, tag_id: int, name: str, slug: str, type: str | None) -> Tag:
        # Vérifier slug conflict sur un autre tag
        existing = await self._repo.get_by_slug(slug)
        if existing is not None and existing.id != tag_id:
            raise TagSlugConflictError(slug)
        updated = await self._repo.update(tag_id, name=name, slug=slug, type=type)
        if updated is None:
            raise TagNotFoundError(tag_id)
        return updated

    async def delete_tag(self, tag_id: int) -> None:
        deleted = await self._repo.soft_delete(tag_id)
        if not deleted:
            raise TagNotFoundError(tag_id)
