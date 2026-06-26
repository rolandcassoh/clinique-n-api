"""Entités domaine page (CMS) — aucune dépendance externe."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Page:
    id: int
    titre: str
    identifiant_url: str
    contenu: str
    titre_meta: str | None
    meta_description: str | None
    est_publie: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def publish(self) -> None:
        self.est_publie = True

    def unpublish(self) -> None:
        self.est_publie = False

    def __str__(self) -> str:
        return f"Page({self.identifiant_url}: {self.titre})"
