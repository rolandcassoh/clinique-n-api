"""Schémas Pydantic v2 — module consultations médicales."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Consultation médicale
# ---------------------------------------------------------------------------

class EncounterCreateRequest(BaseModel):
    id_patient: int
    id_rendez_vous: Optional[int] = None
    motif_principal: Optional[str] = None


class EncounterUpdateRequest(BaseModel):
    date_suivi: Optional[date] = None
    notes_suivi: Optional[str] = None
    statut: Optional[str] = None


class EncounterSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_medecin: int
    id_patient: int
    id_rendez_vous: Optional[int]
    motif_principal: Optional[str]
    date_consultation: datetime
    date_suivi: Optional[date]
    notes_suivi: Optional[str]
    statut: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Rapport médical
# ---------------------------------------------------------------------------

class MedicalReportCreateRequest(BaseModel):
    symptomes: Optional[str] = None
    diagnostic: Optional[str] = None
    traitement: Optional[str] = None
    tension_arterielle: Optional[str] = None
    temperature: Optional[str] = None
    poids: Optional[str] = None
    notes_complementaires: Optional[str] = None


class MedicalReportSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_consultation: int
    symptomes: Optional[str]
    diagnostic: Optional[str]
    traitement: Optional[str]
    tension_arterielle: Optional[str]
    temperature: Optional[str]
    poids: Optional[str]
    notes_complementaires: Optional[str]
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Ordonnance
# ---------------------------------------------------------------------------

class PrescriptionCreateRequest(BaseModel):
    nom_medicament: str = Field(..., min_length=1, max_length=255)
    posologie: Optional[str] = None
    frequence: Optional[str] = None
    duree_jours: Optional[int] = Field(None, gt=0)
    instructions: Optional[str] = None
    est_chronique: bool = False


class PrescriptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_consultation: int
    nom_medicament: str
    posologie: Optional[str]
    frequence: Optional[str]
    duree_jours: Optional[int]
    instructions: Optional[str]
    est_chronique: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Schéma anatomique
# ---------------------------------------------------------------------------

class BodyChartAnnotation(BaseModel):
    x: float
    y: float
    label: str
    color: Optional[str] = "#FF0000"


class BodyChartCreateRequest(BaseModel):
    url_image: str = Field(..., max_length=500)
    annotations: Optional[list[dict[str, Any]]] = None
    notes: Optional[str] = None


class BodyChartSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_rendez_vous: int
    url_image: str
    annotations: Optional[list[dict[str, Any]]]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
