"""Entités domaine langue (language) — aucune dépendance externe."""
from dataclasses import dataclass
from typing import Literal


@dataclass
class Language:
    id: int
    nom: str
    code: str
    nom_natif: str | None
    drapeau: str | None
    est_defaut: bool
    est_actif: bool
    sens_ecriture: Literal["ltr", "rtl"]
