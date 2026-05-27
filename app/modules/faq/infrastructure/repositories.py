"""Implémentation SQLAlchemy async du repository FAQ."""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.faq.domain.entities import FAQ
from app.modules.faq.domain.repositories import FAQRepository
from app.modules.faq.infrastructure.models import FAQModel
from app.shared.schemas.pagination import PaginationParams


def _to_entity(m: FAQModel) -> FAQ:
    return FAQ(
        id=m.id,
        question=m.question,
        answer=m.answer,
        category=m.category,
        is_active=m.is_active,
        sort_order=m.sort_order,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyFAQRepository(FAQRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(
        self, params: PaginationParams, category: str | None = None
    ) -> tuple[list[FAQ], int]:
        base_q = select(FAQModel).where(
            FAQModel.deleted_at.is_(None),
            FAQModel.is_active.is_(True),
        )
        if category:
            base_q = base_q.where(FAQModel.category == category)

        count_q = select(func.count()).select_from(base_q.subquery())
        total: int = (await self._session.execute(count_q)).scalar_one()

        rows_q = (
            base_q.order_by(FAQModel.sort_order, FAQModel.id)
            .offset(params.offset)
            .limit(params.per_page)
        )
        rows = (await self._session.execute(rows_q)).scalars().all()
        return [_to_entity(r) for r in rows], total

    async def get_by_id(self, faq_id: int) -> FAQ | None:
        q = select(FAQModel).where(
            FAQModel.id == faq_id,
            FAQModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def create(
        self,
        question: str,
        answer: str,
        category: str | None,
        is_active: bool,
        sort_order: int,
    ) -> FAQ:
        faq = FAQModel(
            question=question,
            answer=answer,
            category=category,
            is_active=is_active,
            sort_order=sort_order,
        )
        self._session.add(faq)
        await self._session.flush()
        await self._session.refresh(faq)
        return _to_entity(faq)

    async def update(
        self,
        faq_id: int,
        question: str | None,
        answer: str | None,
        category: str | None,
        is_active: bool | None,
        sort_order: int | None,
    ) -> FAQ | None:
        q = select(FAQModel).where(
            FAQModel.id == faq_id,
            FAQModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        if question is not None:
            row.question = question
        if answer is not None:
            row.answer = answer
        if category is not None:
            row.category = category
        if is_active is not None:
            row.is_active = is_active
        if sort_order is not None:
            row.sort_order = sort_order
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def soft_delete(self, faq_id: int) -> bool:
        q = select(FAQModel).where(
            FAQModel.id == faq_id,
            FAQModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        row.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True
