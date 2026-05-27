"""Implémentations SQLAlchemy async des repositories blog."""
from datetime import datetime

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.blog.domain.entities import BlogCategory, BlogPost
from app.modules.blog.domain.repositories import BlogCategoryRepository, BlogPostRepository
from app.modules.blog.infrastructure.models import BlogCategoryModel, BlogPostModel
from app.shared.schemas.pagination import PaginationParams


def _cat_to_entity(m: BlogCategoryModel) -> BlogCategory:
    return BlogCategory(
        id=m.id,
        name=m.name,
        slug=m.slug,
        description=m.description,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _post_to_entity(m: BlogPostModel, author_name: str | None = None) -> BlogPost:
    cat_name: str | None = m.category.name if m.category else None
    return BlogPost(
        id=m.id,
        title=m.title,
        slug=m.slug,
        excerpt=m.excerpt,
        content=m.content,
        author_id=m.author_id,
        author_name=author_name,
        category_id=m.category_id,
        category_name=cat_name,
        thumbnail=m.thumbnail,
        is_published=m.is_published,
        published_at=m.published_at,
        views=m.views,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyBlogCategoryRepository(BlogCategoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[BlogCategory]:
        q = (
            select(BlogCategoryModel)
            .where(BlogCategoryModel.deleted_at.is_(None))
            .order_by(BlogCategoryModel.name)
        )
        rows = (await self._session.execute(q)).scalars().all()
        return [_cat_to_entity(r) for r in rows]

    async def get_by_slug(self, slug: str) -> BlogCategory | None:
        q = select(BlogCategoryModel).where(
            BlogCategoryModel.slug == slug,
            BlogCategoryModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _cat_to_entity(row) if row else None


class SQLAlchemyBlogPostRepository(BlogPostRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _fetch_author_name(self, author_id: int) -> str | None:
        """Récupère le nom de l'auteur depuis la table users."""
        try:
            result = await self._session.execute(
                text("SELECT name FROM users WHERE id = :uid AND deleted_at IS NULL"),
                {"uid": author_id},
            )
            row = result.fetchone()
            return str(row[0]) if row else None
        except Exception:
            return None

    async def list_published(
        self,
        params: PaginationParams,
        category_slug: str | None = None,
        search: str | None = None,
    ) -> tuple[list[BlogPost], int]:
        base_q = (
            select(BlogPostModel)
            .where(
                BlogPostModel.deleted_at.is_(None),
                BlogPostModel.is_published.is_(True),
            )
        )
        if category_slug:
            base_q = base_q.join(BlogCategoryModel).where(
                BlogCategoryModel.slug == category_slug
            )
        if search:
            base_q = base_q.where(
                BlogPostModel.title.ilike(f"%{search}%")
                | BlogPostModel.excerpt.ilike(f"%{search}%")
            )

        count_q = select(func.count()).select_from(base_q.subquery())
        total: int = (await self._session.execute(count_q)).scalar_one()

        rows_q = (
            base_q.order_by(BlogPostModel.published_at.desc())
            .offset(params.offset)
            .limit(params.per_page)
        )
        rows = (await self._session.execute(rows_q)).scalars().all()

        posts: list[BlogPost] = []
        for row in rows:
            author_name = await self._fetch_author_name(row.author_id)
            posts.append(_post_to_entity(row, author_name))

        return posts, total

    async def get_by_slug(self, slug: str) -> BlogPost | None:
        q = select(BlogPostModel).where(
            BlogPostModel.slug == slug,
            BlogPostModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        author_name = await self._fetch_author_name(row.author_id)
        return _post_to_entity(row, author_name)

    async def increment_views(self, post_id: int) -> None:
        stmt = (
            update(BlogPostModel)
            .where(BlogPostModel.id == post_id)
            .values(views=BlogPostModel.views + 1)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def create(
        self,
        title: str,
        slug: str,
        excerpt: str | None,
        content: str,
        author_id: int,
        category_id: int | None,
        thumbnail: str | None,
        is_published: bool,
    ) -> BlogPost:
        post = BlogPostModel(
            title=title,
            slug=slug,
            excerpt=excerpt,
            content=content,
            author_id=author_id,
            category_id=category_id,
            thumbnail=thumbnail,
            is_published=is_published,
            published_at=datetime.utcnow() if is_published else None,
            views=0,
        )
        self._session.add(post)
        await self._session.flush()
        await self._session.refresh(post)
        author_name = await self._fetch_author_name(author_id)
        return _post_to_entity(post, author_name)

    async def update(
        self,
        post_id: int,
        title: str | None,
        slug: str | None,
        excerpt: str | None,
        content: str | None,
        category_id: int | None,
        thumbnail: str | None,
        is_published: bool | None,
    ) -> BlogPost | None:
        q = select(BlogPostModel).where(
            BlogPostModel.id == post_id,
            BlogPostModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None

        if title is not None:
            row.title = title
        if slug is not None:
            row.slug = slug
        if excerpt is not None:
            row.excerpt = excerpt
        if content is not None:
            row.content = content
        if category_id is not None:
            row.category_id = category_id
        if thumbnail is not None:
            row.thumbnail = thumbnail
        if is_published is not None:
            was_published = row.is_published
            row.is_published = is_published
            if is_published and not was_published:
                row.published_at = datetime.utcnow()

        await self._session.flush()
        await self._session.refresh(row)
        author_name = await self._fetch_author_name(row.author_id)
        return _post_to_entity(row, author_name)

    async def soft_delete(self, post_id: int) -> bool:
        q = select(BlogPostModel).where(
            BlogPostModel.id == post_id,
            BlogPostModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        row.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True
