"""Entités domaine slider (bannières défilantes) — aucune dépendance externe."""
from dataclasses import dataclass


@dataclass
class Slider:
    id: int
    titre: str
    sous_titre: str | None
    image: str
    lien: str | None
    texte_bouton: str | None
    position: int
    est_actif: bool
