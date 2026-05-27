"""Interfaces (ABC) des repositories blog."""
from abc import ABC, abstractmethod

from app.modules.blog.domain.entities import BlogCategory, BlogPost
from app.shared.schemas.pagination import PaginationParams


class BlogCategoryRepository(ABC):
    @abstractmethod
    async def list_all(self) -> list[BlogCategory]:
        """Retourne toutes les catégories (non supprimées)."""

    @abstractmethod
    async def get_by_slug(self, slug: str) -> BlogCategory | None:
        """Retourne une catégorie par slug ou None."""


class BlogPostRepository(ABC):
    @abstractmethod
    async def list_published(
        self,
        params: PaginationParams,
        category_slug: str | None = None,
        search: str | None = None,
    ) -> tuple[list[BlogPost], int]:
        """Retourne (posts publiés, total) avec filtres optionnels."""

    @abstractmethod
    async def get_by_slug(self, slug: str) -> BlogPost | None:
        """Retourne un post par slug ou None."""

    @abstractmethod
    async def increment_views(self, post_id: int) -> None:
        """Incrémente le compteur de vues."""

    @abstractmethod
    async def create(
        self,
        title: str,
        slug: str,
        excerpt: str | None,
        content: str,
        author_id: int,
        category_id: int | None,
        thumbnail: str | None,
        is_published: bool,
    ) -> BlogPost:
        """Crée un article."""

    @abstractmethod
    async def update(
        self,
        post_id: int,
        title: str | None,
        slug: str | None,
        excerpt: str | None,
        content: str | None,
        category_id: int | None,
        thumbnail: str | None,
        is_published: bool | None,
    ) -> BlogPost | None:
        """Met à jour un article, retourne None si inexistant."""

    @abstractmethod
    async def soft_delete(self, post_id: int) -> bool:
        """Suppression logique. Retourne True si trouvé."""
