"""Schémas Pydantic v2 du module commission."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CommissionEarningSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    clinic_id: int
    doctor_id: int
    appointment_amount: Decimal
    commission_rate: Decimal
    commission_amount: Decimal
    doctor_earning: Decimal
    status: str
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class EmployeeEarningSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int
    period_start: date
    period_end: date
    total_appointments: int
    gross_amount: Decimal
    commission_deducted: Decimal
    net_amount: Decimal
    status: str
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class DoctorEarningsSummarySchema(BaseModel):
    total_appointments: int
    gross_amount: float
    total_commissions: float
    net_amount: float


class GenerateEarningsReportRequest(BaseModel):
    period_start: date
    period_end: date
    clinic_id: int
    doctor_id: Optional[int] = None
