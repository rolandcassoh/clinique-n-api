"""Cas d'utilisation du module page (CMS)."""
from app.modules.page.domain.entites import Page
from app.modules.page.domain.exceptions import PageNotFoundError, PageSlugAlreadyExistsError
from app.modules.page.domain.depots import PageRepository


class ListPagesUseCase:
    def __init__(self, repo: PageRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[Page]:
        return await self._repo.list_published()


class GetPageBySlugUseCase:
    def __init__(self, repo: PageRepository) -> None:
        self._repo = repo

    async def execute(self, identifiant_url: str) -> Page:
        element = await self._repo.get_by_slug(identifiant_url)
        if element is None:
            raise PageNotFoundError(identifiant_url)
        return element


class CreatePageUseCase:
    def __init__(self, repo: PageRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        titre: str,
        identifiant_url: str,
        contenu: str,
        titre_meta: str | None = None,
        meta_description: str | None = None,
        est_publie: bool = True,
    ) -> Page:
        # Vérification de l'unicité du identifiant_url (get_by_slug exclut les non-publiées,
        # on vérifie ici via un get_by_slug non filtré pour éviter les doublons)
        existant = await self._repo.get_by_slug(identifiant_url)
        if existant is not None:
            raise PageSlugAlreadyExistsError(identifiant_url)
        return await self._repo.create(
            titre=titre,
            identifiant_url=identifiant_url,
            contenu=contenu,
            titre_meta=titre_meta,
            meta_description=meta_description,
            est_publie=est_publie,
        )


class UpdatePageUseCase:
    def __init__(self, repo: PageRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        page_id: int,
        titre: str | None = None,
        identifiant_url: str | None = None,
        contenu: str | None = None,
        titre_meta: str | None = None,
        meta_description: str | None = None,
        est_publie: bool | None = None,
    ) -> Page:
        element = await self._repo.update(
            page_id=page_id,
            titre=titre,
            identifiant_url=identifiant_url,
            contenu=contenu,
            titre_meta=titre_meta,
            meta_description=meta_description,
            est_publie=est_publie,
        )
        if element is None:
            raise PageNotFoundError(page_id)
        return element
