"""Entités domaine billing — ZÉRO import FastAPI/SQLAlchemy."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class BillingStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    CANCELLED = "cancelled"


@dataclass
class BillingItem:
    id: int
    id_facture: int
    description: str
    quantite: int
    prix_unitaire: Decimal
    sous_total: Decimal
    taux_taxe: Decimal
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BillingRecord:
    id: int
    id_rendez_vous: int
    id_patient: int
    reference: str
    sous_total: Decimal
    montant_remise: Decimal
    montant_taxe: Decimal
    total: Decimal
    statut: BillingStatus
    items: list[BillingItem] = field(default_factory=list)
    date_echeance: Optional[date] = None
    paye_le: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_paid(self) -> None:
        if self.statut == BillingStatus.CANCELLED:
            raise ValueError("Impossible de marquer comme payée une facture annulée")
        self.statut = BillingStatus.PAID
        self.paye_le = datetime.utcnow()

    def issue(self) -> None:
        if self.statut != BillingStatus.DRAFT:
            raise ValueError("Seules les factures en brouillon peuvent être émises")
        self.statut = BillingStatus.ISSUED

    def cancel(self) -> None:
        if self.statut == BillingStatus.PAID:
            raise ValueError("Impossible d'annuler une facture déjà payée")
        self.statut = BillingStatus.CANCELLED

    @staticmethod
    def calculate_total(
        sous_total: Decimal,
        montant_remise: Decimal,
        montant_taxe: Decimal,
    ) -> Decimal:
        return sous_total - montant_remise + montant_taxe
