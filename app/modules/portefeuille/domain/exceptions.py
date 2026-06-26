"""Exceptions du domaine portefeuille."""
from __future__ import annotations

from decimal import Decimal

from app.shared.exceptions.domain import DomainException


class WalletNotFoundError(DomainException):
    def __init__(self, id_utilisateur: int) -> None:
        super().__init__(f"Portefeuille de l'utilisateur '{id_utilisateur}' introuvable.")


class InsufficientFundsError(DomainException):
    def __init__(self, solde: Decimal, required: Decimal) -> None:
        super().__init__(
            f"Solde insuffisant : solde actuel {solde} XAF, montant requis {required} XAF."
        )
        self.solde = solde
        self.required = required
