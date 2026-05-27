"""Exceptions domaine commission."""
from __future__ import annotations

from app.shared.exceptions.domain import DomainException


class CommissionNotFoundError(DomainException):
    def __init__(self, commission_id: int) -> None:
        super().__init__(f"Commission with id '{commission_id}' not found.")


class EarningNotFoundError(DomainException):
    def __init__(self, earning_id: int) -> None:
        super().__init__(f"Earning with id '{earning_id}' not found.")


class NoCommissionRateError(DomainException):
    def __init__(self, clinic_id: int) -> None:
        super().__init__(
            f"No active commission rate configured for clinic '{clinic_id}'."
        )
