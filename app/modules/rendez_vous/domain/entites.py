"""Entités du domaine — module rendez-vous. Aucun import FastAPI/SQLAlchemy."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    REFUNDED = "refunded"


class AppointmentType(str, Enum):
    IN_PERSON = "in_person"
    TELECONSULTATION = "teleconsultation"


@dataclass
class Appointment:
    id: int
    reference: str
    id_clinique: int
    id_medecin: int
    id_patient: int
    programme_le: datetime
    duree_minutes: int
    statut: AppointmentStatus
    type: AppointmentType
    montant: Decimal
    montant_avance: Decimal
    statut_paiement: PaymentStatus
    passerelle_paiement: Optional[str] = None
    reference_paiement: Optional[str] = None
    notes: Optional[str] = None
    motif_annulation: Optional[str] = None
    id_evenement_google: Optional[str] = None
    est_suivi: bool = False
    id_rdv_parent: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def confirm(self) -> None:
        if self.statut != AppointmentStatus.PENDING:
            raise ValueError(f"Impossible de confirmer un rendez-vous avec le statut {self.statut}")
        self.statut = AppointmentStatus.CONFIRMED

    def complete(self) -> None:
        if self.statut != AppointmentStatus.CONFIRMED:
            raise ValueError(f"Impossible de compléter un rendez-vous avec le statut {self.statut}")
        self.statut = AppointmentStatus.COMPLETED

    def mark_no_show(self) -> None:
        if self.statut != AppointmentStatus.CONFIRMED:
            raise ValueError(f"Impossible de marquer absent pour le statut {self.statut}")
        self.statut = AppointmentStatus.NO_SHOW

    def cancel(self, motif: str) -> None:
        if self.statut == AppointmentStatus.COMPLETED:
            raise ValueError("Impossible d'annuler un rendez-vous déjà terminé")
        if self.statut == AppointmentStatus.CANCELLED:
            raise ValueError("Ce rendez-vous est déjà annulé")
        self.statut = AppointmentStatus.CANCELLED
        self.motif_annulation = motif

    def is_cancellable_without_charge(self, now: datetime, policy_hours: int = 24) -> bool:
        """Politique d'annulation : remboursement total si annulation > policy_hours avant le RDV."""
        delta = self.programme_le.replace(tzinfo=None) - now.replace(tzinfo=None)
        return delta.total_seconds() / 3600 >= policy_hours

    def calculate_refund_amount(self, now: datetime) -> Decimal:
        """Politique de remboursement : >24h → 100%, 6-24h → 50%, <6h → 0%."""
        heures_avant = (
            self.programme_le.replace(tzinfo=None) - now.replace(tzinfo=None)
        ).total_seconds() / 3600
        if heures_avant >= 24:
            return self.montant
        elif heures_avant >= 6:
            return self.montant * Decimal("0.5")
        else:
            return Decimal("0")


@dataclass
class AppointmentTransaction:
    id: int
    id_rendez_vous: int
    montant: Decimal
    devise: str
    passerelle: str
    reference_transaction: str
    statut: str  # pending | succeeded | failed | refunded (statut de la transaction)
    reponse_passerelle: Optional[dict] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DoctorSlot:
    """Représente un créneau horaire disponible pour un médecin."""
    id_medecin: int
    programme_le: datetime
    duree_minutes: int = 30
    est_disponible: bool = True
