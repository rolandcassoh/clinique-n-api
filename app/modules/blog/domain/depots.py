"""Interfaces (ABC) des repositories blog."""
from abc import ABC, abstractmethod

from app.modules.blog.domain.entites import BlogCategory, BlogPost
from app.shared.schemas.pagination import PaginationParams


class BlogCategoryRepository(ABC):
    @abstractmethod
    async def list_all(self) -> list[BlogCategory]:
        """Retourne toutes les catégories (non supprimées)."""

    @abstractmethod
    async def get_by_slug(self, identifiant_url: str) -> BlogCategory | None:
        """Retourne une catégorie par identifiant_url ou None."""


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
    async def get_by_slug(self, identifiant_url: str) -> BlogPost | None:
        """Retourne un post par identifiant_url ou None."""

    @abstractmethod
    async def increment_views(self, post_id: int) -> None:
        """Incrémente le compteur de vues."""

    @abstractmethod
    async def create(
        self,
        titre: str,
        identifiant_url: str,
        extrait: str | None,
        contenu: str,
        id_auteur: int,
        id_categorie: int | None,
        miniature: str | None,
        est_publie: bool,
    ) -> BlogPost:
        """Crée un article."""

    @abstractmethod
    async def update(
        self,
        post_id: int,
        titre: str | None,
        identifiant_url: str | None,
        extrait: str | None,
        contenu: str | None,
        id_categorie: int | None,
        miniature: str | None,
        est_publie: bool | None,
    ) -> BlogPost | None:
        """Met à jour un article, retourne None si inexistant."""

    @abstractmethod
    async def soft_delete(self, post_id: int) -> bool:
        """Suppression logique. Retourne True si trouvé."""
