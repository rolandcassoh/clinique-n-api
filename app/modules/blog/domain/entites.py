"""Entités domaine blog — aucune dépendance externe."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BlogCategory:
    id: int
    nom: str
    identifiant_url: str
    description: str | None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"BlogCategory({self.identifiant_url}: {self.nom})"


@dataclass
class BlogPost:
    id: int
    titre: str
    identifiant_url: str
    extrait: str | None
    contenu: str
    id_auteur: int
    author_name: str | None  # dénormalisé pour la réponse
    id_categorie: int | None
    category_name: str | None  # dénormalisé pour la réponse
    miniature: str | None
    est_publie: bool
    publie_le: datetime | None
    vues: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def increment_views(self) -> None:
        self.vues += 1

    def publish(self) -> None:
        if not self.est_publie:
            self.est_publie = True
            self.publie_le = datetime.utcnow()

    def __str__(self) -> str:
        return f"BlogPost({self.identifiant_url}: {self.titre})"
