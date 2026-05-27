import math
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.promotion.domain.entities import Promotion, PromotionUse
from app.modules.promotion.domain.repositories import AbstractPromotionRepository
from app.modules.promotion.infrastructure.models import PromotionModel, PromotionUseModel
from app.shared.schemas.pagination import Page, PaginationParams


def _to_entity(m: PromotionModel) -> Promotion:
    return Promotion(
        id=m.id,
        code=m.code,
        name=m.name,
        type=m.type,
        value=m.value,
        min_order_amount=m.min_order_amount,
        max_discount_amount=m.max_discount_amount,
        usage_limit=m.usage_limit,
        usage_count=m.usage_count,
        starts_at=m.starts_at,
        expires_at=m.expires_at,
        is_active=m.is_active,
        applicable_to=m.applicable_to,
        created_at=m.created_at,
        deleted_at=m.deleted_at,
    )


def _use_to_entity(m: PromotionUseModel) -> PromotionUse:
    return PromotionUse(
        id=m.id,
        promotion_id=m.promotion_id,
        user_id=m.user_id,
        order_id=m.order_id,
        appointment_id=m.appointment_id,
        discount_amount=m.discount_amount,
        used_at=m.used_at,
        created_at=m.created_at,
    )


class SQLPromotionRepository(AbstractPromotionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, params: PaginationParams) -> Page[Promotion]:
        count_stmt = select(func.count()).select_from(PromotionModel).where(
            PromotionModel.deleted_at.is_(None)
        )
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = (
            select(PromotionModel)
            .where(PromotionModel.deleted_at.is_(None))
            .order_by(PromotionModel.id.desc())
            .offset(params.offset)
            .limit(params.per_page)
        )
        result = await self._session.execute(stmt)
        data = [_to_entity(m) for m in result.scalars().all()]
        return Page.create(data=data, total=total, params=params)

    async def get_by_id(self, promotion_id: int) -> Promotion | None:
        stmt = select(PromotionModel).where(PromotionModel.id == promotion_id)
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def get_by_code(self, code: str) -> Promotion | None:
        stmt = select(PromotionModel).where(PromotionModel.code == code)
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def create(
        self,
        code: str,
        name: str,
        type: str,
        value: Decimal,
        min_order_amount: Decimal | None,
        max_discount_amount: Decimal | None,
        usage_limit: int | None,
        starts_at: datetime | None,
        expires_at: datetime | None,
        is_active: bool,
        applicable_to: str,
    ) -> Promotion:
        m = PromotionModel(
            code=code,
            name=name,
            type=type,
            value=value,
            min_order_amount=min_order_amount,
            max_discount_amount=max_discount_amount,
            usage_limit=usage_limit,
            usage_count=0,
            starts_at=starts_at,
            expires_at=expires_at,
            is_active=is_active,
            applicable_to=applicable_to,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_entity(m)

    async def update(
        self,
        promotion_id: int,
        code: str,
        name: str,
        type: str,
        value: Decimal,
        min_order_amount: Decimal | None,
        max_discount_amount: Decimal | None,
        usage_limit: int | None,
        starts_at: datetime | None,
        expires_at: datetime | None,
        is_active: bool,
        applicable_to: str,
    ) -> Promotion | None:
        stmt = (
            update(PromotionModel)
            .where(
                PromotionModel.id == promotion_id,
                PromotionModel.deleted_at.is_(None),
            )
            .values(
                code=code,
                name=name,
                type=type,
                value=value,
                min_order_amount=min_order_amount,
                max_discount_amount=max_discount_amount,
                usage_limit=usage_limit,
                starts_at=starts_at,
                expires_at=expires_at,
                is_active=is_active,
                applicable_to=applicable_to,
            )
            .returning(PromotionModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def soft_delete(self, promotion_id: int) -> bool:
        stmt = (
            update(PromotionModel)
            .where(
                PromotionModel.id == promotion_id,
                PromotionModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def list_uses(
        self, promotion_id: int, params: PaginationParams
    ) -> Page[PromotionUse]:
        count_stmt = select(func.count()).select_from(PromotionUseModel).where(
            PromotionUseModel.promotion_id == promotion_id
        )
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = (
            select(PromotionUseModel)
            .where(PromotionUseModel.promotion_id == promotion_id)
            .order_by(PromotionUseModel.used_at.desc())
            .offset(params.offset)
            .limit(params.per_page)
        )
        result = await self._session.execute(stmt)
        data = [_use_to_entity(m) for m in result.scalars().all()]
        return Page.create(data=data, total=total, params=params)
