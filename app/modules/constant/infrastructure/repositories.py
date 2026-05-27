from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.constant.domain.entities import Setting, SettingType
from app.modules.constant.domain.repositories import AbstractSettingRepository
from app.modules.constant.infrastructure.models import SettingModel


def _to_entity(m: SettingModel) -> Setting:
    return Setting(
        id=m.id, key=m.key, raw_value=m.value,
        type=m.type,  # type: ignore[arg-type]
        group=m.group, is_public=m.is_public,
    )


class SQLSettingRepository(AbstractSettingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_public_frontend(self) -> list[Setting]:
        stmt = select(SettingModel).where(
            SettingModel.is_public.is_(True),
            SettingModel.group == "frontend",
        )
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars().all()]

    async def get_public_by_key(self, key: str) -> Setting | None:
        stmt = select(SettingModel).where(
            SettingModel.key == key,
            SettingModel.is_public.is_(True),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def list_all(self) -> list[Setting]:
        stmt = select(SettingModel).order_by(SettingModel.key)
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars().all()]

    async def update_value(self, key: str, value: str | None) -> Setting | None:
        stmt = (
            update(SettingModel)
            .where(SettingModel.key == key)
            .values(value=value)
            .returning(SettingModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None
