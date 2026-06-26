"""Exceptions du domaine facturation."""
from __future__ import annotations

from app.shared.exceptions.domain import DomainException


class BillingNotFoundError(DomainException):
    def __init__(self, id_facture: int) -> None:
        super().__init__(f"Enregistrement de facturation avec l'id '{id_facture}' introuvable.")


class InvoiceAlreadyExistsError(DomainException):
    def __init__(self, id_rendez_vous: int) -> None:
        super().__init__(f"Une facture active existe déjà pour le rendez-vous '{id_rendez_vous}'.")


class InvalidStatusTransitionError(DomainException):
    def __init__(self, current: str, target: str) -> None:
        super().__init__(f"Impossible de passer le statut de facturation de '{current}' à '{target}'.")
