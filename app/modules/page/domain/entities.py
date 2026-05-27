"""Entités domaine page (CMS) — aucune dépendance externe."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Page:
    id: int
    title: str
    slug: str
    content: str
    meta_title: str | None
    meta_description: str | None
    is_published: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def publish(self) -> None:
        self.is_published = True

    def unpublish(self) -> None:
        self.is_published = False

    def __str__(self) -> str:
        return f"Page({self.slug}: {self.title})"
