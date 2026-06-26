"""Entités domaine FAQ — aucune dépendance externe."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FAQ:
    id: int
    question: str
    reponse: str
    category: str | None
    est_actif: bool
    ordre_affichage: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def deactivate(self) -> None:
        self.est_actif = False

    def activate(self) -> None:
        self.est_actif = True

    def __str__(self) -> str:
        return f"FAQ({self.id}: {self.question[:50]})"
