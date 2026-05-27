from abc import ABC, abstractmethod
from typing import Literal

from app.modules.language.domain.entities import Language


class AbstractLanguageRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[Language]:
        ...

    @abstractmethod
    async def get_default(self) -> Language | None:
        ...

    @abstractmethod
    async def get_by_id(self, language_id: int) -> Language | None:
        ...

    @abstractmethod
    async def get_by_code(self, code: str) -> Language | None:
        ...

    @abstractmethod
    async def create(
        self, name: str, code: str, native_name: str | None, flag: str | None,
        is_default: bool, is_active: bool, direction: Literal["ltr", "rtl"]
    ) -> Language:
        ...

    @abstractmethod
    async def update(
        self, language_id: int, name: str, code: str, native_name: str | None,
        flag: str | None, is_default: bool, is_active: bool, direction: Literal["ltr", "rtl"]
    ) -> Language | None:
        ...

    @abstractmethod
    async def set_default(self, language_id: int) -> Language | None:
        ...
