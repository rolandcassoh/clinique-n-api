"""Use Cases du module FAQ."""
from app.modules.faq.domain.entities import FAQ
from app.modules.faq.domain.exceptions import FAQNotFoundError
from app.modules.faq.domain.repositories import FAQRepository
from app.shared.schemas.pagination import Page, PaginationParams


class ListActiveFAQsUseCase:
    def __init__(self, repo: FAQRepository) -> None:
        self._repo = repo

    async def execute(
        self, params: PaginationParams, category: str | None = None
    ) -> Page[FAQ]:
        faqs, total = await self._repo.list_active(params, category)
        return Page.create(data=faqs, total=total, params=params)


class GetFAQUseCase:
    def __init__(self, repo: FAQRepository) -> None:
        self._repo = repo

    async def execute(self, faq_id: int) -> FAQ:
        faq = await self._repo.get_by_id(faq_id)
        if faq is None:
            raise FAQNotFoundError(faq_id)
        return faq


class CreateFAQUseCase:
    def __init__(self, repo: FAQRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        question: str,
        answer: str,
        category: str | None = None,
        is_active: bool = True,
        sort_order: int = 0,
    ) -> FAQ:
        return await self._repo.create(
            question=question,
            answer=answer,
            category=category,
            is_active=is_active,
            sort_order=sort_order,
        )


class UpdateFAQUseCase:
    def __init__(self, repo: FAQRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        faq_id: int,
        question: str | None = None,
        answer: str | None = None,
        category: str | None = None,
        is_active: bool | None = None,
        sort_order: int | None = None,
    ) -> FAQ:
        faq = await self._repo.update(
            faq_id=faq_id,
            question=question,
            answer=answer,
            category=category,
            is_active=is_active,
            sort_order=sort_order,
        )
        if faq is None:
            raise FAQNotFoundError(faq_id)
        return faq


class DeleteFAQUseCase:
    def __init__(self, repo: FAQRepository) -> None:
        self._repo = repo

    async def execute(self, faq_id: int) -> None:
        deleted = await self._repo.soft_delete(faq_id)
        if not deleted:
            raise FAQNotFoundError(faq_id)
