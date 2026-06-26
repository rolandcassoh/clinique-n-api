"""Entités domaine client (customer) — aucune dépendance externe."""
from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class CustomerProfile:
    id: int
    id_utilisateur: int
    nom: str
    courriel: str
    telephone: str | None
    avatar: str | None
    adresse: str | None
    id_ville: int | None
    date_naissance: date | None
    sexe: str | None
    groupe_sanguin: str | None
    biographie: str | None
    created_at: datetime


@dataclass
class FamilyMember:
    id: int
    id_utilisateur: int
    nom: str
    relation: str
    date_naissance: date | None
    sexe: str | None
    groupe_sanguin: str | None
    telephone: str | None
    created_at: datetime
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, now: datetime) -> None:
        self.deleted_at = now

    def belongs_to(self, id_utilisateur: int) -> bool:
        return self.id_utilisateur == id_utilisateur
