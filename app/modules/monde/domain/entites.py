"""Entités domaine world — aucune dépendance externe."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Country:
    id: int
    nom: str
    code_iso2: str
    code_iso3: str
    indicatif_telephone: str
    capitale: str | None
    devise: str | None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"Country({self.code_iso2}: {self.nom})"


@dataclass
class State:
    id: int
    id_pays: int
    nom: str
    code_region: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"State({self.code_region}: {self.nom})"


@dataclass
class City:
    id: int
    id_region: int
    nom: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"City({self.id}: {self.nom})"
