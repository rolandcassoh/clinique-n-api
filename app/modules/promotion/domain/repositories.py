from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from app.modules.promotion.domain.entities import Promotion, PromotionUse
from app.shared.schemas.pagination import Page, PaginationParams


class AbstractPromotionRepository(ABC):
    @abstractmethod
    async def list(self, params: PaginationParams) -> Page[Promotion]:
        ...

    @abstractmethod
    async def get_by_id(self, promotion_id: int) -> Promotion | None:
        ...

    @abstractmethod
    async def get_by_code(self, code: str) -> Promotion | None:
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def soft_delete(self, promotion_id: int) -> bool:
        ...

    @abstractmethod
    async def list_uses(self, promotion_id: int, params: PaginationParams) -> Page[PromotionUse]:
        ...
