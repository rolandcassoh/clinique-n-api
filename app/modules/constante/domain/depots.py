"""Interface (ABC) du repository paramètre (setting)."""
from abc import ABC, abstractmethod

from app.modules.constante.domain.entites import Setting, SettingType


class AbstractSettingRepository(ABC):
    @abstractmethod
    async def list_public_frontend(self) -> list[Setting]:
        """Retourne les paramètres publics du groupe 'frontend'."""
        ...

    @abstractmethod
    async def get_public_by_key(self, cle: str) -> Setting | None:
        """Retourne un paramètre public par sa clé ou None."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Setting]:
        """Retourne tous les paramètres (admin)."""
        ...

    @abstractmethod
    async def update_value(self, cle: str, valeur: str | None) -> Setting | None:
        """Met à jour la valeur d'un paramètre, retourne None si inexistant."""
        ...
