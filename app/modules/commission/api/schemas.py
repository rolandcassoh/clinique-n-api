"""Schémas Pydantic v2 du module commissions."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CommissionEarningSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_rendez_vous: int
    id_clinique: int
    id_medecin: int
    montant_rdv: Decimal
    taux_commission: Decimal
    montant_commission: Decimal
    gain_medecin: Decimal
    statut: str
    paye_le: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class EmployeeEarningSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_medecin: int
    debut_periode: date
    fin_periode: date
    total_rdv: int
    montant_brut: Decimal
    commission_deduite: Decimal
    montant_net: Decimal
    statut: str
    paye_le: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class DoctorEarningsSummarySchema(BaseModel):
    total_rdv: int
    montant_brut: float
    total_commissions: float
    montant_net: float


class GenerateEarningsReportRequest(BaseModel):
    debut_periode: date
    fin_periode: date
    id_clinique: int
    id_medecin: Optional[int] = None
