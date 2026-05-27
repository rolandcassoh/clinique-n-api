"""Use Cases du module blog."""
from app.modules.blog.domain.entities import BlogCategory, BlogPost
from app.modules.blog.domain.exceptions import BlogPostNotFoundError, SlugAlreadyExistsError
from app.modules.blog.domain.repositories import BlogCategoryRepository, BlogPostRepository
from app.shared.schemas.pagination import Page, PaginationParams


class ListBlogCategoriesUseCase:
    def __init__(self, repo: BlogCategoryRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[BlogCategory]:
        return await self._repo.list_all()


class ListPublishedPostsUseCase:
    def __init__(self, repo: BlogPostRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        category_slug: str | None = None,
        search: str | None = None,
    ) -> Page[BlogPost]:
        posts, total = await self._repo.list_published(params, category_slug, search)
        return Page.create(data=posts, total=total, params=params)


class GetBlogPostBySlugUseCase:
    def __init__(self, repo: BlogPostRepository) -> None:
        self._repo = repo

    async def execute(self, slug: str) -> BlogPost:
        post = await self._repo.get_by_slug(slug)
        if post is None:
            raise BlogPostNotFoundError(slug)
        # Incrémente les vues en arrière-plan (sans bloquer la réponse)
        await self._repo.increment_views(post.id)
        post.increment_views()
        return post


class CreateBlogPostUseCase:
    def __init__(self, repo: BlogPostRepository) -> None:
        self._repo = repo

    async def execute(
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
        # Vérification unicité du slug
        existing = await self._repo.get_by_slug(slug)
        if existing is not None:
            raise SlugAlreadyExistsError(slug)
        return await self._repo.create(
            title=title,
            slug=slug,
            excerpt=excerpt,
            content=content,
            author_id=author_id,
            category_id=category_id,
            thumbnail=thumbnail,
            is_published=is_published,
        )


class UpdateBlogPostUseCase:
    def __init__(self, repo: BlogPostRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        post_id: int,
        title: str | None = None,
        slug: str | None = None,
        excerpt: str | None = None,
        content: str | None = None,
        category_id: int | None = None,
        thumbnail: str | None = None,
        is_published: bool | None = None,
    ) -> BlogPost:
        post = await self._repo.update(
            post_id=post_id,
            title=title,
            slug=slug,
            excerpt=excerpt,
            content=content,
            category_id=category_id,
            thumbnail=thumbnail,
            is_published=is_published,
        )
        if post is None:
            raise BlogPostNotFoundError(post_id)
        return post


class DeleteBlogPostUseCase:
    def __init__(self, repo: BlogPostRepository) -> None:
        self._repo = repo

    async def execute(self, post_id: int) -> None:
        deleted = await self._repo.soft_delete(post_id)
        if not deleted:
            raise BlogPostNotFoundError(post_id)
