"""Domain entities — module vital. Zéro import FastAPI/SQLAlchemy."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class VitalSigns:
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
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, now: datetime) -> None:
        self.deleted_at = now

    @property
    def bmi(self) -> Optional[float]:
        """Calcule le BMI si height et weight sont présents."""
        if self.weight is not None and self.height is not None and self.height > 0:
            h_m = float(self.height) / 100.0
            return round(float(self.weight) / (h_m ** 2), 2)
        return None

    def belongs_to(self, patient_id: int) -> bool:
        return self.patient_id == patient_id


@dataclass
class VitalStats:
    """Dernières valeurs de chaque type de constante pour un patient."""
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
