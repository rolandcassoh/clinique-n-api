"""Cas d'utilisation du module FAQ."""
from app.modules.faq.domain.entites import FAQ
from app.modules.faq.domain.exceptions import FAQNotFoundError
from app.modules.faq.domain.depots import FAQRepository
from app.shared.schemas.pagination import Page, PaginationParams


class ListActiveFAQsUseCase:
    def __init__(self, repo: FAQRepository) -> None:
        self._repo = repo

    async def execute(
        self, params: PaginationParams, category: str | None = None
    ) -> Page[FAQ]:
        elements, total = await self._repo.list_active(params, category)
        return Page.create(data=elements, total=total, params=params)


class ListAllFAQsUseCase:
    """Liste toutes les FAQs (actives et inactives) — usage admin."""

    def __init__(self, repo: FAQRepository) -> None:
        self._repo = repo

    async def execute(self, params: PaginationParams) -> Page[FAQ]:
        elements, total = await self._repo.list_all(params)
        return Page.create(data=elements, total=total, params=params)


class GetFAQUseCase:
    def __init__(self, repo: FAQRepository) -> None:
        self._repo = repo

    async def execute(self, faq_id: int) -> FAQ:
        element = await self._repo.get_by_id(faq_id)
        if element is None:
            raise FAQNotFoundError(faq_id)
        return element


class CreateFAQUseCase:
    def __init__(self, repo: FAQRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        question: str,
        reponse: str,
        category: str | None = None,
        est_actif: bool = True,
        ordre_affichage: int = 0,
    ) -> FAQ:
        return await self._repo.create(
            question=question,
            reponse=reponse,
            category=category,
            est_actif=est_actif,
            ordre_affichage=ordre_affichage,
        )


class UpdateFAQUseCase:
    def __init__(self, repo: FAQRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        faq_id: int,
        question: str | None = None,
        reponse: str | None = None,
        category: str | None = None,
        est_actif: bool | None = None,
        ordre_affichage: int | None = None,
    ) -> FAQ:
        element = await self._repo.update(
            faq_id=faq_id,
            question=question,
            reponse=reponse,
            category=category,
            est_actif=est_actif,
            ordre_affichage=ordre_affichage,
        )
        if element is None:
            raise FAQNotFoundError(faq_id)
        return element


class DeleteFAQUseCase:
    def __init__(self, repo: FAQRepository) -> None:
        self._repo = repo

    async def execute(self, faq_id: int) -> None:
        supprime = await self._repo.soft_delete(faq_id)
        if not supprime:
            raise FAQNotFoundError(faq_id)
