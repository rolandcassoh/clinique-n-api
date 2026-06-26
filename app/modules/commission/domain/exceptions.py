"""Exceptions du domaine commission."""
from __future__ import annotations

from app.shared.exceptions.domain import DomainException


class CommissionNotFoundError(DomainException):
    def __init__(self, commission_id: int) -> None:
        super().__init__(f"Commission avec l'id '{commission_id}' introuvable.")


class EarningNotFoundError(DomainException):
    def __init__(self, earning_id: int) -> None:
        super().__init__(f"Revenu avec l'id '{earning_id}' introuvable.")


class NoCommissionRateError(DomainException):
    def __init__(self, id_clinique: int) -> None:
        super().__init__(
            f"Aucun taux de commission actif configuré pour la clinique '{id_clinique}'."
        )
