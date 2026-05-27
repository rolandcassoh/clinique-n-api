"""Entités domaine FAQ — aucune dépendance externe."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FAQ:
    id: int
    question: str
    answer: str
    category: str | None
    is_active: bool
    sort_order: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def __str__(self) -> str:
        return f"FAQ({self.id}: {self.question[:50]})"
