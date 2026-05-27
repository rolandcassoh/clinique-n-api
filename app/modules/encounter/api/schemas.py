"""Schémas Pydantic v2 du module encounter."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Encounter
# ---------------------------------------------------------------------------

class EncounterCreateRequest(BaseModel):
    patient_id: int
    appointment_id: Optional[int] = None
    chief_complaint: Optional[str] = None


class EncounterUpdateRequest(BaseModel):
    follow_up_date: Optional[date] = None
    follow_up_notes: Optional[str] = None
    status: Optional[str] = None


class EncounterSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int
    patient_id: int
    appointment_id: Optional[int]
    chief_complaint: Optional[str]
    encounter_date: datetime
    follow_up_date: Optional[date]
    follow_up_notes: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Medical Report
# ---------------------------------------------------------------------------

class MedicalReportCreateRequest(BaseModel):
    symptoms: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    blood_pressure: Optional[str] = None
    temperature: Optional[str] = None
    weight: Optional[str] = None
    additional_notes: Optional[str] = None


class MedicalReportSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    encounter_id: int
    symptoms: Optional[str]
    diagnosis: Optional[str]
    treatment: Optional[str]
    blood_pressure: Optional[str]
    temperature: Optional[str]
    weight: Optional[str]
    additional_notes: Optional[str]
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Prescription
# ---------------------------------------------------------------------------

class PrescriptionCreateRequest(BaseModel):
    medication_name: str = Field(..., min_length=1, max_length=255)
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration_days: Optional[int] = Field(None, gt=0)
    instructions: Optional[str] = None
    is_chronic: bool = False


class PrescriptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    encounter_id: int
    medication_name: str
    dosage: Optional[str]
    frequency: Optional[str]
    duration_days: Optional[int]
    instructions: Optional[str]
    is_chronic: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Body Chart
# ---------------------------------------------------------------------------

class BodyChartAnnotation(BaseModel):
    x: float
    y: float
    label: str
    color: Optional[str] = "#FF0000"


class BodyChartCreateRequest(BaseModel):
    image_url: str = Field(..., max_length=500)
    annotations: Optional[list[dict[str, Any]]] = None
    notes: Optional[str] = None


class BodyChartSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    image_url: str
    annotations: Optional[list[dict[str, Any]]]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
