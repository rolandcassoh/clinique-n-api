"""Interface (ABC) du repository page."""
from abc import ABC, abstractmethod

from app.modules.page.domain.entites import Page


class PageRepository(ABC):
    @abstractmethod
    async def list_published(self) -> list[Page]:
        """Retourne toutes les pages publiées (sans filtrer le contenu)."""

    @abstractmethod
    async def get_by_slug(self, identifiant_url: str) -> Page | None:
        """Retourne une page publiée par identifiant_url ou None."""

    @abstractmethod
    async def get_by_id(self, page_id: int) -> Page | None:
        """Retourne une page par id (publiée ou non) ou None."""

    @abstractmethod
    async def create(
        self,
        titre: str,
        identifiant_url: str,
        contenu: str,
        titre_meta: str | None,
        meta_description: str | None,
        est_publie: bool,
    ) -> Page:
        """Crée et retourne une page."""

    @abstractmethod
    async def update(
        self,
        page_id: int,
        titre: str | None,
        identifiant_url: str | None,
        contenu: str | None,
        titre_meta: str | None,
        meta_description: str | None,
        est_publie: bool | None,
    ) -> Page | None:
        """Met à jour une page, retourne None si inexistante."""
