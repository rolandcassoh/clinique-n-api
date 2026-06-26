"""Entités domaine tag — aucune dépendance externe."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Tag:
    id: int
    nom: str
    identifiant_url: str
    type: str | None
    created_at: datetime
