"""Modèles SQLAlchemy du module encounter."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.core.crypto.field_encryption import FieldEncryption
from app.shared.models.base import BaseModel
from app.database import Base


# ---------------------------------------------------------------------------
# Type SQLAlchemy chiffré
# ---------------------------------------------------------------------------

class EncryptedText(TypeDecorator):
    """Type SQLAlchemy qui chiffre/déchiffre automatiquement via FieldEncryption."""
    impl = String(2000)
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:  # type: ignore[override]
        return FieldEncryption.encrypt(value) if value else None

    def process_result_value(self, value: str | None, dialect) -> str | None:  # type: ignore[override]
        return FieldEncryption.decrypt(value) if value else None


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

class PatientEncounterModel(BaseModel):
    __tablename__ = "patient_encounters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True, unique=True,
    )
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    encounter_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    follow_up_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("open", "closed", name="encounter_status_enum"),
        nullable=False, default="open",
    )


class EncounterMedicalReportModel(Base):
    __tablename__ = "encounter_medical_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    encounter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patient_encounters.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    symptoms: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    treatment: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    blood_pressure: Mapped[str | None] = mapped_column(String(20), nullable=True)
    temperature: Mapped[str | None] = mapped_column(String(10), nullable=True)
    weight: Mapped[str | None] = mapped_column(String(10), nullable=True)
    additional_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class EncounterPrescriptionModel(BaseModel):
    __tablename__ = "encounter_prescriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    encounter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patient_encounters.id", ondelete="CASCADE"), nullable=False
    )
    medication_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(100), nullable=True)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_chronic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class AppointmentBodyChartModel(BaseModel):
    __tablename__ = "appointment_bodycharts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    annotations: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
