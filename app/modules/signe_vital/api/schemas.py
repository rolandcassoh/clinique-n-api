"""Schémas Pydantic v2 — module constantes vitales."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class VitalSignsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_patient: int
    enregistre_par: Optional[int]
    id_rendez_vous: Optional[int]
    tension_systolique: Optional[int]
    tension_diastolique: Optional[int]
    frequence_cardiaque: Optional[int]
    temperature: Optional[Decimal]
    poids: Optional[Decimal]
    taille: Optional[Decimal]
    saturation_oxygene: Optional[int]
    glycemie: Optional[Decimal]
    notes: Optional[str]
    enregistre_le: datetime
    created_at: datetime
    # IMC calculé à la volée
    bmi: Optional[float] = None


class VitalSignsCreateSchema(BaseModel):
    id_patient: int
    id_rendez_vous: Optional[int] = None
    tension_systolique: Optional[int] = None
    tension_diastolique: Optional[int] = None
    frequence_cardiaque: Optional[int] = None
    temperature: Optional[Decimal] = None
    poids: Optional[Decimal] = None
    taille: Optional[Decimal] = None
    saturation_oxygene: Optional[int] = None
    glycemie: Optional[Decimal] = None
    notes: Optional[str] = None
    enregistre_le: Optional[datetime] = None


class VitalSignsUpdateSchema(BaseModel):
    tension_systolique: Optional[int] = None
    tension_diastolique: Optional[int] = None
    frequence_cardiaque: Optional[int] = None
    temperature: Optional[Decimal] = None
    poids: Optional[Decimal] = None
    taille: Optional[Decimal] = None
    saturation_oxygene: Optional[int] = None
    glycemie: Optional[Decimal] = None
    notes: Optional[str] = None
    enregistre_le: Optional[datetime] = None


class VitalStatsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_patient: int
    last_blood_pressure_systolic: Optional[int] = None
    last_blood_pressure_diastolic: Optional[int] = None
    last_heart_rate: Optional[int] = None
    last_temperature: Optional[Decimal] = None
    last_weight: Optional[Decimal] = None
    last_height: Optional[Decimal] = None
    last_oxygen_saturation: Optional[int] = None
    last_blood_sugar: Optional[Decimal] = None
    last_bmi: Optional[float] = None
