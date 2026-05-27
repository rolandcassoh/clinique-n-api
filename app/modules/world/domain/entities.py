"""Entités domaine world — aucune dépendance externe."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Country:
    id: int
    name: str
    iso2: str
    iso3: str
    phone_code: str
    capital: str | None
    currency: str | None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"Country({self.iso2}: {self.name})"


@dataclass
class State:
    id: int
    country_id: int
    name: str
    state_code: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"State({self.state_code}: {self.name})"


@dataclass
class City:
    id: int
    state_id: int
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"City({self.id}: {self.name})"
