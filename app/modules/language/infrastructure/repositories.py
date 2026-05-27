from typing import Literal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.language.domain.entities import Language
from app.modules.language.domain.repositories import AbstractLanguageRepository
from app.modules.language.infrastructure.models import LanguageModel


def _to_entity(m: LanguageModel) -> Language:
    return Language(
        id=m.id, name=m.name, code=m.code, native_name=m.native_name,
        flag=m.flag, is_default=m.is_default, is_active=m.is_active,
        direction=m.direction,  # type: ignore[arg-type]
    )


class SQLLanguageRepository(AbstractLanguageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[Language]:
        stmt = select(LanguageModel).where(
            LanguageModel.is_active.is_(True),
            LanguageModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars().all()]

    async def get_default(self) -> Language | None:
        stmt = select(LanguageModel).where(
            LanguageModel.is_default.is_(True),
            LanguageModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def get_by_id(self, language_id: int) -> Language | None:
        stmt = select(LanguageModel).where(
            LanguageModel.id == language_id,
            LanguageModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def get_by_code(self, code: str) -> Language | None:
        stmt = select(LanguageModel).where(
            LanguageModel.code == code,
            LanguageModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def create(
        self, name: str, code: str, native_name: str | None, flag: str | None,
        is_default: bool, is_active: bool, direction: Literal["ltr", "rtl"]
    ) -> Language:
        m = LanguageModel(
            name=name, code=code, native_name=native_name, flag=flag,
            is_default=is_default, is_active=is_active, direction=direction,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_entity(m)

    async def update(
        self, language_id: int, name: str, code: str, native_name: str | None,
        flag: str | None, is_default: bool, is_active: bool, direction: Literal["ltr", "rtl"]
    ) -> Language | None:
        stmt = (
            update(LanguageModel)
            .where(LanguageModel.id == language_id, LanguageModel.deleted_at.is_(None))
            .values(
                name=name, code=code, native_name=native_name, flag=flag,
                is_default=is_default, is_active=is_active, direction=direction,
            )
            .returning(LanguageModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def set_default(self, language_id: int) -> Language | None:
        target = await self.get_by_id(language_id)
        if target is None:
            return None

        await self._session.execute(
            update(LanguageModel)
            .where(LanguageModel.deleted_at.is_(None))
            .values(is_default=False)
        )
        stmt = (
            update(LanguageModel)
            .where(LanguageModel.id == language_id)
            .values(is_default=True)
            .returning(LanguageModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None
