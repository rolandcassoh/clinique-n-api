from typing import Any, Generic, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.base import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class CRUDRepository(Generic[ModelT]):
    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, record_id: int) -> ModelT | None:
        result = await self.session.get(self.model, record_id)
        if result and result.is_deleted:
            return None
        return result

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        filters: dict[str, Any] | None = None,
        include_deleted: bool = False,
    ) -> tuple[list[ModelT], int]:
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)

        if not include_deleted:
            stmt = stmt.where(self.model.deleted_at.is_(None))
            count_stmt = count_stmt.where(self.model.deleted_at.is_(None))

        if filters:
            for column, value in filters.items():
                stmt = stmt.where(getattr(self.model, column) == value)
                count_stmt = count_stmt.where(getattr(self.model, column) == value)

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())

        return rows, total

    async def create(self, **data: Any) -> ModelT:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, record_id: int, **data: Any) -> ModelT | None:
        instance = await self.get_by_id(record_id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def soft_delete(self, record_id: int) -> bool:
        instance = await self.get_by_id(record_id)
        if instance is None:
            return False
        instance.soft_delete()
        await self.session.flush()
        return True

    async def hard_delete(self, record_id: int) -> bool:
        instance = await self.session.get(self.model, record_id)
        if instance is None:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True
