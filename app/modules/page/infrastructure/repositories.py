"""Implémentation SQLAlchemy async du repository page."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.page.domain.entities import Page
from app.modules.page.domain.repositories import PageRepository
from app.modules.page.infrastructure.models import PageModel


def _to_entity(m: PageModel) -> Page:
    return Page(
        id=m.id,
        title=m.title,
        slug=m.slug,
        content=m.content,
        meta_title=m.meta_title,
        meta_description=m.meta_description,
        is_published=m.is_published,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyPageRepository(PageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_published(self) -> list[Page]:
        q = (
            select(PageModel)
            .where(
                PageModel.deleted_at.is_(None),
                PageModel.is_published.is_(True),
            )
            .order_by(PageModel.title)
        )
        rows = (await self._session.execute(q)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def get_by_slug(self, slug: str) -> Page | None:
        q = select(PageModel).where(
            PageModel.slug == slug,
            PageModel.deleted_at.is_(None),
            PageModel.is_published.is_(True),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def get_by_id(self, page_id: int) -> Page | None:
        q = select(PageModel).where(
            PageModel.id == page_id,
            PageModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def create(
        self,
        title: str,
        slug: str,
        content: str,
        meta_title: str | None,
        meta_description: str | None,
        is_published: bool,
    ) -> Page:
        page = PageModel(
            title=title,
            slug=slug,
            content=content,
            meta_title=meta_title,
            meta_description=meta_description,
            is_published=is_published,
        )
        self._session.add(page)
        await self._session.flush()
        await self._session.refresh(page)
        return _to_entity(page)

    async def update(
        self,
        page_id: int,
        title: str | None,
        slug: str | None,
        content: str | None,
        meta_title: str | None,
        meta_description: str | None,
        is_published: bool | None,
    ) -> Page | None:
        q = select(PageModel).where(
            PageModel.id == page_id,
            PageModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None

        if title is not None:
            row.title = title
        if slug is not None:
            row.slug = slug
        if content is not None:
            row.content = content
        if meta_title is not None:
            row.meta_title = meta_title
        if meta_description is not None:
            row.meta_description = meta_description
        if is_published is not None:
            row.is_published = is_published

        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)
