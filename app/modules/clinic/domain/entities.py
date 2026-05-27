"""Domain entities — module clinic. Zéro import FastAPI/SQLAlchemy."""
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional


# ── Clinic ────────────────────────────────────────────────────────────────────

@dataclass
class ClinicCategory:
    id: int
    name: str
    slug: str
    image: Optional[str]
    description: Optional[str]
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


@dataclass
class Clinic:
    id: int
    owner_id: int
    name: str
    slug: str
    description: Optional[str]
    address: Optional[str]
    city_id: Optional[int]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    logo: Optional[str]
    cover_image: Optional[str]
    is_active: bool
    is_featured: bool
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    commission_rate: Decimal
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, now: datetime) -> None:
        self.deleted_at = now

    def toggle_active(self) -> None:
        self.is_active = not self.is_active


@dataclass
class ClinicService:
    id: int
    clinic_id: int
    name: str
    description: Optional[str]
    price: Decimal
    duration_minutes: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


# ── Doctor ────────────────────────────────────────────────────────────────────

@dataclass
class TimeSlot:
    start: datetime
    end: datetime

    def overlaps(self, other: "TimeSlot") -> bool:
        return self.start < other.end and self.end > other.start


@dataclass
class DoctorSession:
    id: int
    doctor_id: int
    day_of_week: int  # 0=Lundi, 6=Dimanche
    start_time: time
    end_time: time
    slot_duration_minutes: int
    max_patients_per_slot: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def generate_theoretical_slots(self, for_date: date) -> list[datetime]:
        """Génère tous les créneaux théoriques pour une date donnée."""
        slots = []
        slot_start = datetime.combine(for_date, self.start_time)
        slot_end_limit = datetime.combine(for_date, self.end_time)
        delta = timedelta(minutes=self.slot_duration_minutes)
        while slot_start + delta <= slot_end_limit:
            slots.append(slot_start)
            slot_start += delta
        return slots


@dataclass
class DoctorLeave:
    id: int
    doctor_id: int
    leave_date: date
    reason: Optional[str]
    is_full_day: bool
    start_time: Optional[time]
    end_time: Optional[time]
    created_at: datetime
    updated_at: datetime


@dataclass
class DoctorRating:
    id: int
    doctor_id: int
    user_id: int
    appointment_id: Optional[int]
    rating: int  # 1-5
    comment: Optional[str]
    is_approved: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def validate(self) -> None:
        if not (1 <= self.rating <= 5):
            raise ValueError(f"Rating must be between 1 and 5, got {self.rating}")


@dataclass
class Doctor:
    id: int
    user_id: int
    clinic_id: int
    speciality: Optional[str]
    qualification: Optional[str]
    experience_years: int
    consultation_fee: Decimal
    advance_payment_amount: Decimal
    is_available: bool
    google_calendar_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    # Enrichissement optionnel
    average_rating: Optional[float] = None
    sessions: list[DoctorSession] = field(default_factory=list)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, now: datetime) -> None:
        self.deleted_at = now

    def toggle_availability(self) -> None:
        self.is_available = not self.is_available


@dataclass
class Receptionist:
    id: int
    user_id: int
    clinic_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
