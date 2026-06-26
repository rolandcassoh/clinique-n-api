"""Entités domaine wallet — ZÉRO import FastAPI/SQLAlchemy."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from app.modules.portefeuille.domain.exceptions import InsufficientFundsError


class TransactionType(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"


@dataclass
class WalletTransaction:
    """Transaction de portefeuille (non persistée directement — créée par les entités)."""
    type: str                        # 'credit' | 'debit'
    montant: Decimal
    solde_apres: Decimal
    description: str = ""
    reference: Optional[str] = None


@dataclass
class PatientWallet:
    """Portefeuille prépayé d'un patient."""
    id: int
    id_utilisateur: int
    solde: Decimal
    devise: str = "XAF"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def credit(self, montant: Decimal, description: str = "", reference: Optional[str] = None) -> WalletTransaction:
        if montant <= Decimal("0"):
            raise ValueError("Le montant du crédit doit être positif")
        self.solde += montant
        return WalletTransaction(
            type=TransactionType.CREDIT.valeur,
            montant=montant,
            solde_apres=self.solde,
            description=description,
            reference=reference,
        )

    def debit(self, montant: Decimal, description: str = "", reference: Optional[str] = None) -> WalletTransaction:
        if montant <= Decimal("0"):
            raise ValueError("Le montant du débit doit être positif")
        if self.solde < montant:
            raise InsufficientFundsError(self.solde, montant)
        self.solde -= montant
        return WalletTransaction(
            type=TransactionType.DEBIT.valeur,
            montant=montant,
            solde_apres=self.solde,
            description=description,
            reference=reference,
        )


@dataclass
class WalletHistory:
    """Entrée d'historique de transaction."""
    id: int
    id_portefeuille: int
    montant: Decimal
    type: str
    reference: Optional[str]
    description: Optional[str]
    solde_apres: Decimal
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
