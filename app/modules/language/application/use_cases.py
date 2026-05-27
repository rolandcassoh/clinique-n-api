from typing import Literal

from app.modules.language.domain.entities import Language
from app.modules.language.domain.exceptions import LanguageCodeConflictError, LanguageNotFoundError
from app.modules.language.domain.repositories import AbstractLanguageRepository


class LanguageUseCases:
    def __init__(self, repo: AbstractLanguageRepository) -> None:
        self._repo = repo

    async def list_active(self) -> list[Language]:
        return await self._repo.list_active()

    async def get_default(self) -> Language:
        language = await self._repo.get_default()
        if language is None:
            raise LanguageNotFoundError("default")
        return language

    async def create_language(
        self, name: str, code: str, native_name: str | None, flag: str | None,
        is_default: bool, is_active: bool, direction: Literal["ltr", "rtl"]
    ) -> Language:
        existing = await self._repo.get_by_code(code)
        if existing is not None:
            raise LanguageCodeConflictError(code)
        return await self._repo.create(
            name=name, code=code, native_name=native_name, flag=flag,
            is_default=is_default, is_active=is_active, direction=direction,
        )

    async def update_language(
        self, language_id: int, name: str, code: str, native_name: str | None,
        flag: str | None, is_default: bool, is_active: bool, direction: Literal["ltr", "rtl"]
    ) -> Language:
        existing = await self._repo.get_by_code(code)
        if existing is not None and existing.id != language_id:
            raise LanguageCodeConflictError(code)
        updated = await self._repo.update(
            language_id, name=name, code=code, native_name=native_name, flag=flag,
            is_default=is_default, is_active=is_active, direction=direction,
        )
        if updated is None:
            raise LanguageNotFoundError(language_id)
        return updated

    async def set_default(self, language_id: int) -> Language:
        language = await self._repo.set_default(language_id)
        if language is None:
            raise LanguageNotFoundError(language_id)
        return language
