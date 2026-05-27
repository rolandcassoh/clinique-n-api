"""Use Cases du module page (CMS)."""
from app.modules.page.domain.entities import Page
from app.modules.page.domain.exceptions import PageNotFoundError, PageSlugAlreadyExistsError
from app.modules.page.domain.repositories import PageRepository


class ListPagesUseCase:
    def __init__(self, repo: PageRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[Page]:
        return await self._repo.list_published()


class GetPageBySlugUseCase:
    def __init__(self, repo: PageRepository) -> None:
        self._repo = repo

    async def execute(self, slug: str) -> Page:
        page = await self._repo.get_by_slug(slug)
        if page is None:
            raise PageNotFoundError(slug)
        return page


class CreatePageUseCase:
    def __init__(self, repo: PageRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        title: str,
        slug: str,
        content: str,
        meta_title: str | None = None,
        meta_description: str | None = None,
        is_published: bool = True,
    ) -> Page:
        # Vérification unicité slug (get_by_slug ignore les non-publiées, on vérifie par get_by_id via slug via repo)
        # On tente la création et laisse la contrainte DB lever l'erreur le cas échéant,
        # ou on peut faire un get explicite. Ici on fait un get_by_slug non filtré.
        existing = await self._repo.get_by_slug(slug)
        if existing is not None:
            raise PageSlugAlreadyExistsError(slug)
        return await self._repo.create(
            title=title,
            slug=slug,
            content=content,
            meta_title=meta_title,
            meta_description=meta_description,
            is_published=is_published,
        )


class UpdatePageUseCase:
    def __init__(self, repo: PageRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        page_id: int,
        title: str | None = None,
        slug: str | None = None,
        content: str | None = None,
        meta_title: str | None = None,
        meta_description: str | None = None,
        is_published: bool | None = None,
    ) -> Page:
        page = await self._repo.update(
            page_id=page_id,
            title=title,
            slug=slug,
            content=content,
            meta_title=meta_title,
            meta_description=meta_description,
            is_published=is_published,
        )
        if page is None:
            raise PageNotFoundError(page_id)
        return page
