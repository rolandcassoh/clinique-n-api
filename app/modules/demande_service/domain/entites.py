"""Entités domaine RequestService — pur Python, aucune dépendance externe."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum


class RequestServiceStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    MATCHED = "matched"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class RequestService:
    id: int
    id_utilisateur: int
    id_categorie: int | None
    titre: str
    description: str
    localisation: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    budget_min: Decimal | None
    budget_max: Decimal | None
    preferred_date: date | None
    creneau_prefere: time | None
    statut: RequestServiceStatus
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def can_cancel(self) -> bool:
        """Un patient ne peut annuler que si la demande est en statut 'pending'."""
        return self.statut == RequestServiceStatus.PENDING

    def cancel(self) -> None:
        if not self.can_cancel:
            raise ValueError(
                f"Impossible d'annuler une demande avec le statut '{self.statut.value}'. "
                "Seules les demandes en statut 'pending' peuvent être annulées."
            )
        self.statut = RequestServiceStatus.CANCELLED

    def __str__(self) -> str:
        return f"RequestService({self.id}: {self.titre[:50]} [{self.statut.value}])"
