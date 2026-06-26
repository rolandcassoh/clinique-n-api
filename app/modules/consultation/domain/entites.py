"""Entités du domaine — module consultations médicales. Aucun import FastAPI/SQLAlchemy."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional


class EncounterStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class PatientEncounter:
    """Consultation médicale."""
    id: int
    id_medecin: int
    id_patient: int
    statut: EncounterStatus
    id_rendez_vous: Optional[int] = None
    motif_principal: Optional[str] = None
    date_consultation: datetime = field(default_factory=datetime.utcnow)
    date_suivi: Optional[date] = None
    notes_suivi: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def close(self) -> None:
        self.statut = EncounterStatus.CLOSED

    def reopen(self) -> None:
        self.statut = EncounterStatus.OPEN


@dataclass
class MedicalReport:
    """Rapport médical lié à une consultation (champs sensibles chiffrés en DB)."""
    id: int
    id_consultation: int
    symptomes: Optional[str] = None        # symptômes (valeur déchiffrée en mémoire)
    diagnostic: Optional[str] = None       # diagnostic (valeur déchiffrée en mémoire)
    traitement: Optional[str] = None       # traitement (valeur déchiffrée en mémoire)
    tension_arterielle: Optional[str] = None
    temperature: Optional[str] = None
    poids: Optional[str] = None
    notes_complementaires: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Prescription:
    """Ordonnance médicale."""
    id: int
    id_consultation: int
    nom_medicament: str
    posologie: Optional[str] = None
    frequence: Optional[str] = None
    duree_jours: Optional[int] = None
    instructions: Optional[str] = None
    est_chronique: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BodyChart:
    """Schéma anatomique annoté lié à un rendez-vous."""
    id: int
    id_rendez_vous: int
    url_image: str
    annotations: Optional[list[dict[str, Any]]] = None   # [{x, y, libelle, couleur}]
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
