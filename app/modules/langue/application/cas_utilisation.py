"""Cas d'utilisation du module langue (language)."""
from typing import Literal

from app.modules.langue.domain.entites import Language
from app.modules.langue.domain.exceptions import LanguageCodeConflictError, LanguageNotFoundError
from app.modules.langue.domain.depots import AbstractLanguageRepository


class LanguageUseCases:
    def __init__(self, repo: AbstractLanguageRepository) -> None:
        self._repo = repo

    async def list_active(self) -> list[Language]:
        return await self._repo.list_active()

    async def get_default(self) -> Language:
        langue = await self._repo.get_default()
        if langue is None:
            raise LanguageNotFoundError("default")
        return langue

    async def create_language(
        self, nom: str, code: str, nom_natif: str | None, drapeau: str | None,
        est_defaut: bool, est_actif: bool, sens_ecriture: Literal["ltr", "rtl"]
    ) -> Language:
        existante = await self._repo.get_by_code(code)
        if existante is not None:
            raise LanguageCodeConflictError(code)
        return await self._repo.create(
            nom=nom, code=code, nom_natif=nom_natif, drapeau=drapeau,
            est_defaut=est_defaut, est_actif=est_actif, sens_ecriture=sens_ecriture,
        )

    async def update_language(
        self, language_id: int, nom: str, code: str, nom_natif: str | None,
        drapeau: str | None, est_defaut: bool, est_actif: bool, sens_ecriture: Literal["ltr", "rtl"]
    ) -> Language:
        existante = await self._repo.get_by_code(code)
        if existante is not None and existante.id != language_id:
            raise LanguageCodeConflictError(code)
        mise_a_jour = await self._repo.update(
            language_id, nom=nom, code=code, nom_natif=nom_natif, drapeau=drapeau,
            est_defaut=est_defaut, est_actif=est_actif, sens_ecriture=sens_ecriture,
        )
        if mise_a_jour is None:
            raise LanguageNotFoundError(language_id)
        return mise_a_jour

    async def set_default(self, language_id: int) -> Language:
        langue = await self._repo.set_default(language_id)
        if langue is None:
            raise LanguageNotFoundError(language_id)
        return langue
