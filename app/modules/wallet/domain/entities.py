"""Entités domaine wallet — ZÉRO import FastAPI/SQLAlchemy."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from app.modules.wallet.domain.exceptions import InsufficientFundsError


class TransactionType(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"


@dataclass
class WalletTransaction:
    """Transaction de portefeuille (non persistée directement — créée par les entités)."""
    type: str                        # 'credit' | 'debit'
    amount: Decimal
    balance_after: Decimal
    description: str = ""
    reference: Optional[str] = None


@dataclass
class PatientWallet:
    """Portefeuille prépayé d'un patient."""
    id: int
    user_id: int
    balance: Decimal
    currency: str = "XAF"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def credit(self, amount: Decimal, description: str = "", reference: Optional[str] = None) -> WalletTransaction:
        if amount <= Decimal("0"):
            raise ValueError("Credit amount must be positive")
        self.balance += amount
        return WalletTransaction(
            type=TransactionType.CREDIT.value,
            amount=amount,
            balance_after=self.balance,
            description=description,
            reference=reference,
        )

    def debit(self, amount: Decimal, description: str = "", reference: Optional[str] = None) -> WalletTransaction:
        if amount <= Decimal("0"):
            raise ValueError("Debit amount must be positive")
        if self.balance < amount:
            raise InsufficientFundsError(self.balance, amount)
        self.balance -= amount
        return WalletTransaction(
            type=TransactionType.DEBIT.value,
            amount=amount,
            balance_after=self.balance,
            description=description,
            reference=reference,
        )


@dataclass
class WalletHistory:
    """Entrée d'historique de transaction."""
    id: int
    wallet_id: int
    amount: Decimal
    type: str
    reference: Optional[str]
    description: Optional[str]
    balance_after: Decimal
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
