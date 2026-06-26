"""Entités domaine commission — ZÉRO import FastAPI/SQLAlchemy."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class CommissionType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class CommissionStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"


class EarningStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"


@dataclass
class EmployeeCommission:
    """Taux de commission d'une clinique pour un médecin (ou taux général)."""
    id: int
    id_clinique: int
    taux_commission: Decimal
    type: CommissionType
    est_actif: bool = True
    id_medecin: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CommissionEarning:
    """Commission calculée pour un rendez-vous complété."""
    id: int
    id_rendez_vous: int
    id_clinique: int
    id_medecin: int
    montant_rdv: Decimal
    taux_commission: Decimal
    montant_commission: Decimal
    gain_medecin: Decimal
    statut: CommissionStatus = CommissionStatus.PENDING
    paye_le: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_paid(self) -> None:
        self.statut = CommissionStatus.PAID
        self.paye_le = datetime.utcnow()

    @staticmethod
    def calculate(
        montant_rdv: Decimal,
        taux_commission: Decimal,
        commission_type: CommissionType,
    ) -> tuple[Decimal, Decimal]:
        """Retourne (montant_commission, gain_medecin)."""
        if commission_type == CommissionType.PERCENTAGE:
            montant_commission = (montant_rdv * taux_commission / Decimal("100")).quantize(
                Decimal("0.01")
            )
        else:
            montant_commission = taux_commission.quantize(Decimal("0.01"))
        gain_medecin = montant_rdv - montant_commission
        return montant_commission, gain_medecin


@dataclass
class EmployeeEarning:
    """Rapport agrégé des revenus d'un médecin pour une période."""
    id: int
    id_medecin: int
    debut_periode: date
    fin_periode: date
    total_rdv: int
    montant_brut: Decimal
    commission_deduite: Decimal
    montant_net: Decimal
    statut: EarningStatus = EarningStatus.PENDING
    paye_le: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
