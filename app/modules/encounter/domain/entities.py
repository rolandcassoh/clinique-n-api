"""Entités domaine encounter — ZÉRO import FastAPI/SQLAlchemy."""
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
    doctor_id: int
    patient_id: int
    status: EncounterStatus
    appointment_id: Optional[int] = None
    chief_complaint: Optional[str] = None
    encounter_date: datetime = field(default_factory=datetime.utcnow)
    follow_up_date: Optional[date] = None
    follow_up_notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def close(self) -> None:
        self.status = EncounterStatus.CLOSED

    def reopen(self) -> None:
        self.status = EncounterStatus.OPEN


@dataclass
class MedicalReport:
    """Rapport médical lié à une consultation (champs sensibles chiffrés en DB)."""
    id: int
    encounter_id: int
    symptoms: Optional[str] = None        # valeur déchiffrée en mémoire
    diagnosis: Optional[str] = None       # valeur déchiffrée en mémoire
    treatment: Optional[str] = None       # valeur déchiffrée en mémoire
    blood_pressure: Optional[str] = None
    temperature: Optional[str] = None
    weight: Optional[str] = None
    additional_notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Prescription:
    """Ordonnance médicale."""
    id: int
    encounter_id: int
    medication_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration_days: Optional[int] = None
    instructions: Optional[str] = None
    is_chronic: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BodyChart:
    """Schéma anatomique annoté lié à un rendez-vous."""
    id: int
    appointment_id: int
    image_url: str
    annotations: Optional[list[dict[str, Any]]] = None   # [{x, y, label, color}]
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
