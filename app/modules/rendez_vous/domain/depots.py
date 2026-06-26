"""Ports (ABC) repositories du module appointment — Python pur."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app.modules.rendez_vous.domain.entites import Appointment, AppointmentTransaction
from app.shared.schemas.pagination import PaginationParams


class AppointmentRepository(ABC):
    @abstractmethod
    async def save(self, appointment: Appointment) -> Appointment:
        """Crée ou met à jour un rendez-vous."""

    @abstractmethod
    async def find_by_id(self, id_rendez_vous: int) -> Optional[Appointment]:
        """Retourne le rendez-vous ou None."""

    @abstractmethod
    async def find_by_reference(self, reference: str) -> Optional[Appointment]:
        """Retourne le rendez-vous par sa référence unique."""

    @abstractmethod
    async def list_for_patient(
        self,
        id_patient: int,
        params: PaginationParams,
        statut: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[list[Appointment], int]:
        """Liste paginée pour un patient."""

    @abstractmethod
    async def list_for_doctor(
        self,
        id_medecin: int,
        params: PaginationParams,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        statut: Optional[str] = None,
    ) -> tuple[list[Appointment], int]:
        """Liste paginée pour un médecin."""

    @abstractmethod
    async def list_all(
        self,
        params: PaginationParams,
        statut: Optional[str] = None,
        id_medecin: Optional[int] = None,
        id_patient: Optional[int] = None,
        id_clinique: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[list[Appointment], int]:
        """Liste admin, tous RDVs."""

    @abstractmethod
    async def get_booked_slots(
        self, id_medecin: int, day: date
    ) -> list[datetime]:
        """Retourne les créneaux déjà pris (CONFIRMED + PENDING) pour un médecin un jour donné."""

    @abstractmethod
    async def count_by_status(self, id_clinique: Optional[int] = None) -> dict[str, int]:
        """Statistiques : nombre de RDVs par statut."""

    @abstractmethod
    async def sum_revenue(
        self, id_clinique: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Decimal:
        """Revenu total (statut_paiement = paid)."""

    @abstractmethod
    async def soft_delete(self, id_rendez_vous: int) -> bool:
        """Soft-delete."""


class AppointmentTransactionRepository(ABC):
    @abstractmethod
    async def create(
        self,
        id_rendez_vous: int,
        montant: Decimal,
        devise: str,
        passerelle: str,
        reference_transaction: str,
        statut: str,
        reponse_passerelle: Optional[dict] = None,
    ) -> AppointmentTransaction:
        """Crée une transaction."""

    @abstractmethod
    async def list_for_appointment(
        self, id_rendez_vous: int
    ) -> list[AppointmentTransaction]:
        """Liste les transactions d'un RDV."""

    @abstractmethod
    async def update_status(
        self, reference_transaction: str, statut: str, reponse_passerelle: Optional[dict] = None
    ) -> Optional[AppointmentTransaction]:
        """Met à jour le statut d'une transaction."""
