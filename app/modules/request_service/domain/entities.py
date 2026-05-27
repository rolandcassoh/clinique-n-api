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
    user_id: int
    category_id: int | None
    title: str
    description: str
    location: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    budget_min: Decimal | None
    budget_max: Decimal | None
    preferred_date: date | None
    preferred_time: time | None
    status: RequestServiceStatus
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def can_cancel(self) -> bool:
        """Un patient ne peut annuler que si la demande est en statut 'pending'."""
        return self.status == RequestServiceStatus.PENDING

    def cancel(self) -> None:
        if not self.can_cancel:
            raise ValueError(
                f"Cannot cancel a request with status '{self.status.value}'. "
                "Only 'pending' requests can be cancelled."
            )
        self.status = RequestServiceStatus.CANCELLED

    def __str__(self) -> str:
        return f"RequestService({self.id}: {self.title[:50]} [{self.status.value}])"
