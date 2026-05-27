"""Exceptions domaine appointment."""
from __future__ import annotations

from datetime import datetime

from app.shared.exceptions.domain import BusinessRuleViolationError, ConflictError


class SlotNotAvailableError(BusinessRuleViolationError):
    def __init__(self, scheduled_at: datetime) -> None:
        super().__init__(
            f"Le créneau {scheduled_at.isoformat()} n'est pas disponible."
        )
        self.scheduled_at = scheduled_at


class AppointmentNotFoundError(BusinessRuleViolationError):
    def __init__(self, appointment_id: int) -> None:
        super().__init__(f"Rendez-vous {appointment_id} introuvable.")
        self.appointment_id = appointment_id


class AppointmentPermissionError(BusinessRuleViolationError):
    def __init__(self, message: str = "Action non autorisée sur ce rendez-vous.") -> None:
        super().__init__(message)


class PaymentAlreadyProcessedError(ConflictError):
    def __init__(self, appointment_id: int) -> None:
        super().__init__(
            f"Le paiement du rendez-vous {appointment_id} a déjà été traité."
        )


class InvalidPaymentGatewayError(BusinessRuleViolationError):
    def __init__(self, gateway: str) -> None:
        super().__init__(f"Passerelle de paiement invalide : {gateway}")
