"""Modèles SQLAlchemy du module appointment."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.shared.models.base import BaseModel


class AppointmentModel(BaseModel):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reference: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    clinic_id: Mapped[int] = mapped_column(Integer, nullable=False)
    doctor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    patient_id: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "confirmed",
            "cancelled",
            "completed",
            "no_show",
            name="appointment_status_enum",
            native_enum=False,
        ),
        default="pending",
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        Enum(
            "in_person",
            "teleconsultation",
            name="appointment_type_enum",
            native_enum=False,
        ),
        default="in_person",
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False
    )
    advance_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False
    )
    payment_status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "partial",
            "paid",
            "refunded",
            name="apt_payment_status_enum",
            native_enum=False,
        ),
        default="pending",
        nullable=False,
    )
    payment_gateway: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_followup: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parent_appointment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("appointments.id"), nullable=True
    )

    # Relations
    transactions: Mapped[list["AppointmentTransactionModel"]] = relationship(
        "AppointmentTransactionModel",
        back_populates="appointment",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    parent: Mapped["AppointmentModel | None"] = relationship(
        "AppointmentModel",
        remote_side="AppointmentModel.id",
        foreign_keys=[parent_appointment_id],
    )


class AppointmentTransactionModel(Base):
    __tablename__ = "appointment_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("appointments.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="XAF", nullable=False)
    gateway: Mapped[str] = mapped_column(String(50), nullable=False)
    transaction_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "succeeded",
            "failed",
            "refunded",
            name="apt_tx_status_enum",
            native_enum=False,
        ),
        default="pending",
        nullable=False,
    )
    gateway_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    appointment: Mapped["AppointmentModel"] = relationship(
        "AppointmentModel", back_populates="transactions"
    )
