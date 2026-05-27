"""Interfaces (ABC) des repositories FAQ."""
from abc import ABC, abstractmethod

from app.modules.faq.domain.entities import FAQ
from app.shared.schemas.pagination import PaginationParams


class FAQRepository(ABC):
    @abstractmethod
    async def list_active(
        self, params: PaginationParams, category: str | None = None
    ) -> tuple[list[FAQ], int]:
        """Retourne (FAQs actives, total) — filtre optionnel par catégorie."""

    @abstractmethod
    async def get_by_id(self, faq_id: int) -> FAQ | None:
        """Retourne une FAQ (active ou non) par id, ou None."""

    @abstractmethod
    async def create(
        self,
        question: str,
        answer: str,
        category: str | None,
        is_active: bool,
        sort_order: int,
    ) -> FAQ:
        """Crée et retourne une nouvelle FAQ."""

    @abstractmethod
    async def update(
        self,
        faq_id: int,
        question: str | None,
        answer: str | None,
        category: str | None,
        is_active: bool | None,
        sort_order: int | None,
    ) -> FAQ | None:
        """Met à jour et retourne la FAQ, ou None si inexistante."""

    @abstractmethod
    async def soft_delete(self, faq_id: int) -> bool:
        """Supprime logiquement. Retourne True si trouvée, False sinon."""
