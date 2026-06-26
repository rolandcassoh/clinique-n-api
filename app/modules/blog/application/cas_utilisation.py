"""Cas d'utilisation du module blog."""
from app.modules.blog.domain.entites import BlogCategory, BlogPost
from app.modules.blog.domain.exceptions import BlogPostNotFoundError, SlugAlreadyExistsError
from app.modules.blog.domain.depots import BlogCategoryRepository, BlogPostRepository
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
        articles, total = await self._repo.list_published(params, category_slug, search)
        return Page.create(data=articles, total=total, params=params)


class GetBlogPostBySlugUseCase:
    def __init__(self, repo: BlogPostRepository) -> None:
        self._repo = repo

    async def execute(self, identifiant_url: str) -> BlogPost:
        article = await self._repo.get_by_slug(identifiant_url)
        if article is None:
            raise BlogPostNotFoundError(identifiant_url)
        # Incrémente les vues en arrière-plan (sans bloquer la réponse)
        await self._repo.increment_views(article.id)
        article.increment_views()
        return article


class CreateBlogPostUseCase:
    def __init__(self, repo: BlogPostRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        titre: str,
        identifiant_url: str,
        extrait: str | None,
        contenu: str,
        id_auteur: int,
        id_categorie: int | None,
        miniature: str | None,
        est_publie: bool,
    ) -> BlogPost:
        # Vérification de l'unicité du identifiant_url
        existant = await self._repo.get_by_slug(identifiant_url)
        if existant is not None:
            raise SlugAlreadyExistsError(identifiant_url)
        return await self._repo.create(
            titre=titre,
            identifiant_url=identifiant_url,
            extrait=extrait,
            contenu=contenu,
            id_auteur=id_auteur,
            id_categorie=id_categorie,
            miniature=miniature,
            est_publie=est_publie,
        )


class UpdateBlogPostUseCase:
    def __init__(self, repo: BlogPostRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        post_id: int,
        titre: str | None = None,
        identifiant_url: str | None = None,
        extrait: str | None = None,
        contenu: str | None = None,
        id_categorie: int | None = None,
        miniature: str | None = None,
        est_publie: bool | None = None,
    ) -> BlogPost:
        article = await self._repo.update(
            post_id=post_id,
            titre=titre,
            identifiant_url=identifiant_url,
            extrait=extrait,
            contenu=contenu,
            id_categorie=id_categorie,
            miniature=miniature,
            est_publie=est_publie,
        )
        if article is None:
            raise BlogPostNotFoundError(post_id)
        return article


class DeleteBlogPostUseCase:
    def __init__(self, repo: BlogPostRepository) -> None:
        self._repo = repo

    async def execute(self, post_id: int) -> None:
        supprime = await self._repo.soft_delete(post_id)
        if not supprime:
            raise BlogPostNotFoundError(post_id)
