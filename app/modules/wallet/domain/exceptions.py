"""Exceptions domaine wallet."""
from __future__ import annotations

from decimal import Decimal

from app.shared.exceptions.domain import DomainException


class WalletNotFoundError(DomainException):
    def __init__(self, user_id: int) -> None:
        super().__init__(f"Wallet for user '{user_id}' not found.")


class InsufficientFundsError(DomainException):
    def __init__(self, balance: Decimal, required: Decimal) -> None:
        super().__init__(
            f"Insufficient funds: balance is {balance} XAF, required {required} XAF."
        )
        self.balance = balance
        self.required = required
