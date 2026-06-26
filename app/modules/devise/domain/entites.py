"""Entités domaine devise (devise) — aucune dépendance externe."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Currency:
    id: int
    nom: str
    code: str
    symbole: str
    taux_change: Decimal
    est_defaut: bool
    est_actif: bool

    def set_default(self) -> None:
        self.est_defaut = True

    def unset_default(self) -> None:
        self.est_defaut = False
