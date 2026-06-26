"""Entités domaine tax — aucune dépendance externe."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Tax:
    id: int
    nom: str
    tarif: Decimal
    type: str  # 'percentage' | 'fixed'
    id_pays: int | None
    est_defaut: bool
    est_actif: bool
    created_at: datetime
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
