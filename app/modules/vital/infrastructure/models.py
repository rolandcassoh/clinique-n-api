"""SQLAlchemy models — module vital."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class VitalSignsModel(BaseModel):
    __tablename__ = "vital_signs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recorded_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    appointment_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blood_pressure_systolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blood_pressure_diastolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temperature: Mapped[Decimal | None] = mapped_column(DECIMAL(4, 1), nullable=True)
    weight: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    height: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    oxygen_saturation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blood_sugar: Mapped[Decimal | None] = mapped_column(DECIMAL(6, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
