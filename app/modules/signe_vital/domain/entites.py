"""Entités du domaine — module constantes vitales. Aucun import FastAPI/SQLAlchemy."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class VitalSigns:
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
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, now: datetime) -> None:
        self.deleted_at = now

    @property
    def bmi(self) -> Optional[float]:
        """Calcule l'IMC si la taille et le poids sont renseignés."""
        if self.poids is not None and self.taille is not None and self.taille > 0:
            taille_m = float(self.taille) / 100.0
            return round(float(self.poids) / (taille_m ** 2), 2)
        return None

    def belongs_to(self, id_patient: int) -> bool:
        return self.id_patient == id_patient


@dataclass
class VitalStats:
    """Dernières valeurs de chaque type de constante vitale pour un patient."""
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
