"""Exceptions domaine billing."""
from __future__ import annotations

from app.shared.exceptions.domain import DomainException


class BillingNotFoundError(DomainException):
    def __init__(self, billing_id: int) -> None:
        super().__init__(f"Billing record with id '{billing_id}' not found.")


class InvoiceAlreadyExistsError(DomainException):
    def __init__(self, appointment_id: int) -> None:
        super().__init__(f"An active invoice already exists for appointment '{appointment_id}'.")


class InvalidStatusTransitionError(DomainException):
    def __init__(self, current: str, target: str) -> None:
        super().__init__(f"Cannot transition billing status from '{current}' to '{target}'.")
