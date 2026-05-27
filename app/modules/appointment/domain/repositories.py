"""Ports (ABC) repositories du module appointment — Python pur."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app.modules.appointment.domain.entities import Appointment, AppointmentTransaction
from app.shared.schemas.pagination import PaginationParams


class AppointmentRepository(ABC):
    @abstractmethod
    async def save(self, appointment: Appointment) -> Appointment:
        """Crée ou met à jour un rendez-vous."""

    @abstractmethod
    async def find_by_id(self, appointment_id: int) -> Optional[Appointment]:
        """Retourne le rendez-vous ou None."""

    @abstractmethod
    async def find_by_reference(self, reference: str) -> Optional[Appointment]:
        """Retourne le rendez-vous par sa référence unique."""

    @abstractmethod
    async def list_for_patient(
        self,
        patient_id: int,
        params: PaginationParams,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[list[Appointment], int]:
        """Liste paginée pour un patient."""

    @abstractmethod
    async def list_for_doctor(
        self,
        doctor_id: int,
        params: PaginationParams,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> tuple[list[Appointment], int]:
        """Liste paginée pour un médecin."""

    @abstractmethod
    async def list_all(
        self,
        params: PaginationParams,
        status: Optional[str] = None,
        doctor_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        clinic_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[list[Appointment], int]:
        """Liste admin, tous RDVs."""

    @abstractmethod
    async def get_booked_slots(
        self, doctor_id: int, day: date
    ) -> list[datetime]:
        """Retourne les créneaux déjà pris (CONFIRMED + PENDING) pour un médecin un jour donné."""

    @abstractmethod
    async def count_by_status(self, clinic_id: Optional[int] = None) -> dict[str, int]:
        """Statistiques : nombre de RDVs par statut."""

    @abstractmethod
    async def sum_revenue(
        self, clinic_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Decimal:
        """Revenu total (payment_status = paid)."""

    @abstractmethod
    async def soft_delete(self, appointment_id: int) -> bool:
        """Soft-delete."""


class AppointmentTransactionRepository(ABC):
    @abstractmethod
    async def create(
        self,
        appointment_id: int,
        amount: Decimal,
        currency: str,
        gateway: str,
        transaction_ref: str,
        status: str,
        gateway_response: Optional[dict] = None,
    ) -> AppointmentTransaction:
        """Crée une transaction."""

    @abstractmethod
    async def list_for_appointment(
        self, appointment_id: int
    ) -> list[AppointmentTransaction]:
        """Liste les transactions d'un RDV."""

    @abstractmethod
    async def update_status(
        self, transaction_ref: str, status: str, gateway_response: Optional[dict] = None
    ) -> Optional[AppointmentTransaction]:
        """Met à jour le statut d'une transaction."""
