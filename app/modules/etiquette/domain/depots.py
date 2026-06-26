"""Interface (ABC) du repository tag."""
from abc import ABC, abstractmethod

from app.modules.etiquette.domain.entites import Tag


class AbstractTagRepository(ABC):
    @abstractmethod
    async def list(self, type_filter: str | None = None, search: str | None = None) -> list[Tag]:
        """Retourne la liste des étiquettes avec filtres optionnels."""
        ...

    @abstractmethod
    async def get_by_id(self, tag_id: int) -> Tag | None:
        """Retourne une étiquette par son id ou None."""
        ...

    @abstractmethod
    async def get_by_slug(self, identifiant_url: str) -> Tag | None:
        """Retourne une étiquette par son identifiant_url ou None."""
        ...

    @abstractmethod
    async def create(self, nom: str, identifiant_url: str, type: str | None) -> Tag:
        """Crée et retourne une nouvelle étiquette."""
        ...

    @abstractmethod
    async def update(self, tag_id: int, nom: str, identifiant_url: str, type: str | None) -> Tag | None:
        """Met à jour une étiquette, retourne None si inexistante."""
        ...

    @abstractmethod
    async def soft_delete(self, tag_id: int) -> bool:
        """Suppression logique. Retourne True si trouvée, False sinon."""
        ...
