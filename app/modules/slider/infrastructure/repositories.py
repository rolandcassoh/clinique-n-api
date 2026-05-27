from datetime import datetime, timezone

from sqlalchemy import asc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.slider.domain.entities import Slider
from app.modules.slider.domain.repositories import AbstractSliderRepository
from app.modules.slider.infrastructure.models import SliderModel


def _to_entity(m: SliderModel) -> Slider:
    return Slider(
        id=m.id, title=m.title, subtitle=m.subtitle, image=m.image,
        link=m.link, button_text=m.button_text, position=m.position, is_active=m.is_active,
    )


class SQLSliderRepository(AbstractSliderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[Slider]:
        stmt = (
            select(SliderModel)
            .where(SliderModel.is_active.is_(True), SliderModel.deleted_at.is_(None))
            .order_by(asc(SliderModel.position))
        )
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars().all()]

    async def get_by_id(self, slider_id: int) -> Slider | None:
        stmt = select(SliderModel).where(
            SliderModel.id == slider_id, SliderModel.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def create(
        self, title: str, subtitle: str | None, image: str, link: str | None,
        button_text: str | None, position: int, is_active: bool
    ) -> Slider:
        m = SliderModel(
            title=title, subtitle=subtitle, image=image, link=link,
            button_text=button_text, position=position, is_active=is_active,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_entity(m)

    async def update(
        self, slider_id: int, title: str, subtitle: str | None, image: str,
        link: str | None, button_text: str | None, position: int, is_active: bool
    ) -> Slider | None:
        stmt = (
            update(SliderModel)
            .where(SliderModel.id == slider_id, SliderModel.deleted_at.is_(None))
            .values(
                title=title, subtitle=subtitle, image=image, link=link,
                button_text=button_text, position=position, is_active=is_active,
            )
            .returning(SliderModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def reorder(self, slider_id: int, position: int) -> Slider | None:
        stmt = (
            update(SliderModel)
            .where(SliderModel.id == slider_id, SliderModel.deleted_at.is_(None))
            .values(position=position)
            .returning(SliderModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def soft_delete(self, slider_id: int) -> bool:
        stmt = (
            update(SliderModel)
            .where(SliderModel.id == slider_id, SliderModel.deleted_at.is_(None))
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0
