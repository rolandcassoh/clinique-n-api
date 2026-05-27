"""Pydantic v2 schemas — module vital."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class VitalSignsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    recorded_by: Optional[int]
    appointment_id: Optional[int]
    blood_pressure_systolic: Optional[int]
    blood_pressure_diastolic: Optional[int]
    heart_rate: Optional[int]
    temperature: Optional[Decimal]
    weight: Optional[Decimal]
    height: Optional[Decimal]
    oxygen_saturation: Optional[int]
    blood_sugar: Optional[Decimal]
    notes: Optional[str]
    recorded_at: datetime
    created_at: datetime
    # BMI calculé à la volée
    bmi: Optional[float] = None


class VitalSignsCreateSchema(BaseModel):
    patient_id: int
    appointment_id: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    height: Optional[Decimal] = None
    oxygen_saturation: Optional[int] = None
    blood_sugar: Optional[Decimal] = None
    notes: Optional[str] = None
    recorded_at: Optional[datetime] = None


class VitalSignsUpdateSchema(BaseModel):
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    height: Optional[Decimal] = None
    oxygen_saturation: Optional[int] = None
    blood_sugar: Optional[Decimal] = None
    notes: Optional[str] = None
    recorded_at: Optional[datetime] = None


class VitalStatsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: int
    last_blood_pressure_systolic: Optional[int] = None
    last_blood_pressure_diastolic: Optional[int] = None
    last_heart_rate: Optional[int] = None
    last_temperature: Optional[Decimal] = None
    last_weight: Optional[Decimal] = None
    last_height: Optional[Decimal] = None
    last_oxygen_saturation: Optional[int] = None
    last_blood_sugar: Optional[Decimal] = None
    last_bmi: Optional[float] = None
