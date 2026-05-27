from abc import ABC, abstractmethod

from app.modules.slider.domain.entities import Slider


class AbstractSliderRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[Slider]:
        ...

    @abstractmethod
    async def get_by_id(self, slider_id: int) -> Slider | None:
        ...

    @abstractmethod
    async def create(
        self, title: str, subtitle: str | None, image: str, link: str | None,
        button_text: str | None, position: int, is_active: bool
    ) -> Slider:
        ...

    @abstractmethod
    async def update(
        self, slider_id: int, title: str, subtitle: str | None, image: str,
        link: str | None, button_text: str | None, position: int, is_active: bool
    ) -> Slider | None:
        ...

    @abstractmethod
    async def reorder(self, slider_id: int, position: int) -> Slider | None:
        ...

    @abstractmethod
    async def soft_delete(self, slider_id: int) -> bool:
        ...
