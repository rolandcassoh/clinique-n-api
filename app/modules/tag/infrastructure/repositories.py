from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tag.domain.entities import Tag
from app.modules.tag.domain.repositories import AbstractTagRepository
from app.modules.tag.infrastructure.models import TagModel


def _to_entity(m: TagModel) -> Tag:
    return Tag(id=m.id, name=m.name, slug=m.slug, type=m.type, created_at=m.created_at)


class SQLTagRepository(AbstractTagRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, type_filter: str | None = None, search: str | None = None) -> list[Tag]:
        stmt = select(TagModel).where(TagModel.deleted_at.is_(None))
        if type_filter:
            stmt = stmt.where(TagModel.type == type_filter)
        if search:
            stmt = stmt.where(TagModel.name.ilike(f"%{search}%"))
        stmt = stmt.limit(100)
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars().all()]

    async def get_by_id(self, tag_id: int) -> Tag | None:
        stmt = select(TagModel).where(TagModel.id == tag_id, TagModel.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def get_by_slug(self, slug: str) -> Tag | None:
        stmt = select(TagModel).where(TagModel.slug == slug, TagModel.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def create(self, name: str, slug: str, type: str | None) -> Tag:
        m = TagModel(name=name, slug=slug, type=type)
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_entity(m)

    async def update(self, tag_id: int, name: str, slug: str, type: str | None) -> Tag | None:
        stmt = (
            update(TagModel)
            .where(TagModel.id == tag_id, TagModel.deleted_at.is_(None))
            .values(name=name, slug=slug, type=type)
            .returning(TagModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def soft_delete(self, tag_id: int) -> bool:
        stmt = (
            update(TagModel)
            .where(TagModel.id == tag_id, TagModel.deleted_at.is_(None))
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0
