from typing import Any

from app.modules.constant.domain.entities import Setting
from app.modules.constant.domain.exceptions import SettingNotFoundError
from app.modules.constant.domain.repositories import AbstractSettingRepository


class ConstantUseCases:
    def __init__(self, repo: AbstractSettingRepository) -> None:
        self._repo = repo

    async def get_public_frontend_constants(self) -> dict[str, Any]:
        settings = await self._repo.list_public_frontend()
        return {s.key: s.value for s in settings}

    async def get_public_constant(self, key: str) -> dict[str, Any]:
        setting = await self._repo.get_public_by_key(key)
        if setting is None:
            raise SettingNotFoundError(key)
        return {"key": setting.key, "value": setting.value}

    async def list_all_settings(self) -> list[Setting]:
        return await self._repo.list_all()

    async def update_setting(self, key: str, value: str | None) -> Setting:
        setting = await self._repo.update_value(key, value)
        if setting is None:
            raise SettingNotFoundError(key)
        return setting
