"""Exceptions domaine appointment."""
from __future__ import annotations

from datetime import datetime

from app.shared.exceptions.domain import BusinessRuleViolationError, ConflictError


class SlotNotAvailableError(BusinessRuleViolationError):
    def __init__(self, programme_le: datetime) -> None:
        super().__init__(
            f"Le créneau {programme_le.isoformat()} n'est pas disponible."
        )
        self.programme_le = programme_le


class AppointmentNotFoundError(BusinessRuleViolationError):
    def __init__(self, id_rendez_vous: int) -> None:
        super().__init__(f"Rendez-vous {id_rendez_vous} introuvable.")
        self.id_rendez_vous = id_rendez_vous


class AppointmentPermissionError(BusinessRuleViolationError):
    def __init__(self, message: str = "Action non autorisée sur ce rendez-vous.") -> None:
        super().__init__(message)


class PaymentAlreadyProcessedError(ConflictError):
    def __init__(self, id_rendez_vous: int) -> None:
        super().__init__(
            f"Le paiement du rendez-vous {id_rendez_vous} a déjà été traité."
        )


class InvalidPaymentGatewayError(BusinessRuleViolationError):
    def __init__(self, passerelle: str) -> None:
        super().__init__(f"Passerelle de paiement invalide : {passerelle}")
