"""Entités domaine blog — aucune dépendance externe."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BlogCategory:
    id: int
    name: str
    slug: str
    description: str | None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"BlogCategory({self.slug}: {self.name})"


@dataclass
class BlogPost:
    id: int
    title: str
    slug: str
    excerpt: str | None
    content: str
    author_id: int
    author_name: str | None  # dénormalisé pour la réponse
    category_id: int | None
    category_name: str | None  # dénormalisé pour la réponse
    thumbnail: str | None
    is_published: bool
    published_at: datetime | None
    views: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def increment_views(self) -> None:
        self.views += 1

    def publish(self) -> None:
        if not self.is_published:
            self.is_published = True
            self.published_at = datetime.utcnow()

    def __str__(self) -> str:
        return f"BlogPost({self.slug}: {self.title})"
