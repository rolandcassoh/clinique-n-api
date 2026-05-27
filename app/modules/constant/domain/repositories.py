from abc import ABC, abstractmethod

from app.modules.constant.domain.entities import Setting, SettingType


class AbstractSettingRepository(ABC):
    @abstractmethod
    async def list_public_frontend(self) -> list[Setting]:
        """Settings publics du groupe 'frontend'."""
        ...

    @abstractmethod
    async def get_public_by_key(self, key: str) -> Setting | None:
        ...

    @abstractmethod
    async def list_all(self) -> list[Setting]:
        ...

    @abstractmethod
    async def update_value(self, key: str, value: str | None) -> Setting | None:
        ...
