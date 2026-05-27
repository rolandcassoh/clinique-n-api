from app.modules.slider.domain.entities import Slider
from app.modules.slider.domain.exceptions import SliderNotFoundError
from app.modules.slider.domain.repositories import AbstractSliderRepository


class SliderUseCases:
    def __init__(self, repo: AbstractSliderRepository) -> None:
        self._repo = repo

    async def list_active(self) -> list[Slider]:
        return await self._repo.list_active()

    async def create_slider(
        self, title: str, subtitle: str | None, image: str, link: str | None,
        button_text: str | None, position: int = 0, is_active: bool = True
    ) -> Slider:
        return await self._repo.create(
            title=title, subtitle=subtitle, image=image, link=link,
            button_text=button_text, position=position, is_active=is_active,
        )

    async def update_slider(
        self, slider_id: int, title: str, subtitle: str | None, image: str,
        link: str | None, button_text: str | None, position: int, is_active: bool
    ) -> Slider:
        updated = await self._repo.update(
            slider_id, title=title, subtitle=subtitle, image=image, link=link,
            button_text=button_text, position=position, is_active=is_active,
        )
        if updated is None:
            raise SliderNotFoundError(slider_id)
        return updated

    async def reorder_slider(self, slider_id: int, position: int) -> Slider:
        slider = await self._repo.reorder(slider_id, position)
        if slider is None:
            raise SliderNotFoundError(slider_id)
        return slider

    async def delete_slider(self, slider_id: int) -> None:
        deleted = await self._repo.soft_delete(slider_id)
        if not deleted:
            raise SliderNotFoundError(slider_id)
