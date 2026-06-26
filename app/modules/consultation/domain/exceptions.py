"""Exceptions du domaine — module consultations médicales."""
from __future__ import annotations

from app.shared.exceptions.domain import DomainException


class EncounterNotFoundError(DomainException):
    def __init__(self, id_consultation: int) -> None:
        super().__init__(f"Consultation médicale '{id_consultation}' introuvable.")


class MedicalReportNotFoundError(DomainException):
    def __init__(self, id_consultation: int) -> None:
        super().__init__(f"Rapport médical de la consultation '{id_consultation}' introuvable.")


class PrescriptionNotFoundError(DomainException):
    def __init__(self, prescription_id: int) -> None:
        super().__init__(f"Ordonnance '{prescription_id}' introuvable.")


class BodyChartNotFoundError(DomainException):
    def __init__(self, id_rendez_vous: int) -> None:
        super().__init__(f"Schéma anatomique du rendez-vous '{id_rendez_vous}' introuvable.")


class UnauthorizedMedicalAccessError(DomainException):
    def __init__(self) -> None:
        super().__init__("L'accès aux données médicales est réservé au médecin traitant.")
