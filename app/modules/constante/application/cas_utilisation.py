"""Cas d'utilisation du module constant (paramètres système)."""
from typing import Any

from app.modules.constante.domain.entites import Setting
from app.modules.constante.domain.exceptions import SettingNotFoundError
from app.modules.constante.domain.depots import AbstractSettingRepository


class ConstantUseCases:
    def __init__(self, repo: AbstractSettingRepository) -> None:
        self._repo = repo

    async def get_public_frontend_constants(self) -> dict[str, Any]:
        """Retourne un dictionnaire clé→valeur des paramètres publics frontend."""
        parametres = await self._repo.list_public_frontend()
        return {s.cle: s.valeur for s in parametres}

    async def get_public_constant(self, cle: str) -> dict[str, Any]:
        """Retourne un paramètre public par sa clé."""
        parametre = await self._repo.get_public_by_key(cle)
        if parametre is None:
            raise SettingNotFoundError(cle)
        return {"cle": parametre.cle, "valeur": parametre.valeur}

    async def list_all_settings(self) -> list[Setting]:
        """Retourne tous les paramètres (usage admin)."""
        return await self._repo.list_all()

    async def update_setting(self, cle: str, valeur: str | None) -> Setting:
        """Met à jour la valeur d'un paramètre."""
        parametre = await self._repo.update_value(cle, valeur)
        if parametre is None:
            raise SettingNotFoundError(cle)
        return parametre
