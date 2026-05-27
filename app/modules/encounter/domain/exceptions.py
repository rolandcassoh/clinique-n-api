"""Exceptions domaine encounter."""
from __future__ import annotations

from app.shared.exceptions.domain import DomainException


class EncounterNotFoundError(DomainException):
    def __init__(self, encounter_id: int) -> None:
        super().__init__(f"Encounter with id '{encounter_id}' not found.")


class MedicalReportNotFoundError(DomainException):
    def __init__(self, encounter_id: int) -> None:
        super().__init__(f"Medical report for encounter '{encounter_id}' not found.")


class PrescriptionNotFoundError(DomainException):
    def __init__(self, prescription_id: int) -> None:
        super().__init__(f"Prescription with id '{prescription_id}' not found.")


class BodyChartNotFoundError(DomainException):
    def __init__(self, appointment_id: int) -> None:
        super().__init__(f"Body chart for appointment '{appointment_id}' not found.")


class UnauthorizedMedicalAccessError(DomainException):
    def __init__(self) -> None:
        super().__init__("Access to medical data is restricted to the treating doctor.")
