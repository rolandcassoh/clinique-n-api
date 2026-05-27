"""Interface (ABC) du repository page."""
from abc import ABC, abstractmethod

from app.modules.page.domain.entities import Page


class PageRepository(ABC):
    @abstractmethod
    async def list_published(self) -> list[Page]:
        """Retourne toutes les pages publiées (sans filtrer le content)."""

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Page | None:
        """Retourne une page publiée par slug ou None."""

    @abstractmethod
    async def get_by_id(self, page_id: int) -> Page | None:
        """Retourne une page par id (publiée ou non) ou None."""

    @abstractmethod
    async def create(
        self,
        title: str,
        slug: str,
        content: str,
        meta_title: str | None,
        meta_description: str | None,
        is_published: bool,
    ) -> Page:
        """Crée et retourne une page."""

    @abstractmethod
    async def update(
        self,
        page_id: int,
        title: str | None,
        slug: str | None,
        content: str | None,
        meta_title: str | None,
        meta_description: str | None,
        is_published: bool | None,
    ) -> Page | None:
        """Met à jour une page, retourne None si inexistante."""
