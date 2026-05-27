"""Modèles SQLAlchemy du module commission."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class EmployeeCommissionModel(BaseModel):
    __tablename__ = "employee_commissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clinic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    doctor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("percentage", "fixed", name="commission_type_enum"),
        nullable=False, default="percentage",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CommissionEarningModel(BaseModel):
    __tablename__ = "commission_earnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("appointments.id", ondelete="RESTRICT"), nullable=False
    )
    clinic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clinics.id", ondelete="RESTRICT"), nullable=False
    )
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    appointment_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    doctor_earning: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "paid", name="commission_earning_status_enum"),
        nullable=False, default="pending",
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class EmployeeEarningModel(BaseModel):
    __tablename__ = "employee_earnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    total_appointments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    commission_deducted: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        Enum("pending", "paid", name="employee_earning_status_enum"),
        nullable=False, default="pending",
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
