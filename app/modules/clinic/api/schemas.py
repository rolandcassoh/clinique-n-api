"""Pydantic v2 schemas — module clinic."""
from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── ClinicCategory ────────────────────────────────────────────────────────────

class ClinicCategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    image: Optional[str]
    description: Optional[str]
    is_active: bool
    sort_order: int
    created_at: datetime


class ClinicCategoryCreateSchema(BaseModel):
    name: str
    slug: str
    image: Optional[str] = None
    description: Optional[str] = None


class ClinicCategoryUpdateSchema(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


# ── Clinic ────────────────────────────────────────────────────────────────────

class ClinicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class ClinicCreateSchema(BaseModel):
    owner_id: int
    name: str
    slug: str
    description: Optional[str] = None
    address: Optional[str] = None
    city_id: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo: Optional[str] = None
    cover_image: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    commission_rate: Decimal = Decimal("0")


class ClinicUpdateSchema(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city_id: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo: Optional[str] = None
    cover_image: Optional[str] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    commission_rate: Optional[Decimal] = None


# ── ClinicService ─────────────────────────────────────────────────────────────

class ClinicServiceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clinic_id: int
    name: str
    description: Optional[str]
    price: Decimal
    duration_minutes: int
    is_active: bool
    created_at: datetime


class ClinicServiceCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal = Decimal("0")
    duration_minutes: int = 30


class ClinicServiceUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None


# ── Doctor ────────────────────────────────────────────────────────────────────

class DoctorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    clinic_id: int
    speciality: Optional[str]
    qualification: Optional[str]
    experience_years: int
    consultation_fee: Decimal
    advance_payment_amount: Decimal
    is_available: bool
    average_rating: Optional[float]
    created_at: datetime
    updated_at: datetime


class DoctorCreateSchema(BaseModel):
    user_id: int
    speciality: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: int = 0
    consultation_fee: Decimal = Decimal("0")
    advance_payment_amount: Decimal = Decimal("0")


class DoctorUpdateSchema(BaseModel):
    speciality: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[Decimal] = None
    advance_payment_amount: Optional[Decimal] = None
    is_available: Optional[bool] = None


class DoctorAvailabilitySchema(BaseModel):
    is_available: bool


# ── DoctorSession ─────────────────────────────────────────────────────────────

class DoctorSessionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int
    day_of_week: int
    start_time: time
    end_time: time
    slot_duration_minutes: int
    max_patients_per_slot: int
    is_active: bool
    created_at: datetime


class DoctorSessionCreateSchema(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: time
    end_time: time
    slot_duration_minutes: int = 30
    max_patients_per_slot: int = 1


class DoctorSessionUpdateSchema(BaseModel):
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    slot_duration_minutes: Optional[int] = None
    max_patients_per_slot: Optional[int] = None
    is_active: Optional[bool] = None


# ── DoctorLeave ───────────────────────────────────────────────────────────────

class DoctorLeaveSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int
    leave_date: date
    reason: Optional[str]
    is_full_day: bool
    start_time: Optional[time]
    end_time: Optional[time]
    created_at: datetime


class DoctorLeaveCreateSchema(BaseModel):
    leave_date: date
    reason: Optional[str] = None
    is_full_day: bool = True
    start_time: Optional[time] = None
    end_time: Optional[time] = None


# ── DoctorRating ──────────────────────────────────────────────────────────────

class DoctorRatingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int
    user_id: int
    appointment_id: Optional[int]
    rating: int
    comment: Optional[str]
    is_approved: bool
    created_at: datetime


class DoctorRatingCreateSchema(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    appointment_id: Optional[int] = None


# ── Receptionist ──────────────────────────────────────────────────────────────

class ReceptionistSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    clinic_id: int
    is_active: bool
    created_at: datetime


class ReceptionistCreateSchema(BaseModel):
    user_id: int


# ── Slots ─────────────────────────────────────────────────────────────────────

class AvailableSlotsSchema(BaseModel):
    doctor_id: int
    date: date
    slots: list[datetime]
