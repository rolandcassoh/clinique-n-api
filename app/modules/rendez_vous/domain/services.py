"""Services du domaine — module rendez-vous. Python pur, sans dépendances externes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.rendez_vous.domain.entites import Appointment


@dataclass
class CancellationResult:
    is_full_refund: bool
    refund_amount: Decimal
    policy_applied: str  # 'full' | 'partial' | 'none' (politique appliquée)


class CancellationPolicyService:
    """Évalue la politique de remboursement selon les règles de la clinique."""

    def evaluate(self, appointment: "Appointment", now: datetime) -> CancellationResult:
        montant_remboursement = appointment.calculate_refund_amount(now)
        if montant_remboursement == appointment.montant:
            politique = "full"
            remboursement_total = True
        elif montant_remboursement > Decimal("0"):
            politique = "partial"
            remboursement_total = False
        else:
            politique = "none"
            remboursement_total = False
        return CancellationResult(
            is_full_refund=remboursement_total,
            refund_amount=montant_remboursement,
            policy_applied=politique,
        )


class SlotAvailabilityService:
    """
    Service qui calcule les créneaux disponibles pour un médecin un jour donné.
    Prend en entrée les créneaux déjà réservés et génère les créneaux libres.
    """

    DEFAULT_START_HOUR: int = 8
    DEFAULT_END_HOUR: int = 18

    def get_available_slots(
        self,
        day: date,
        booked_slots: list[datetime],
        duree_minutes: int = 30,
        start_hour: int = DEFAULT_START_HOUR,
        end_hour: int = DEFAULT_END_HOUR,
    ) -> list[datetime]:
        """
        Génère tous les créneaux de la journée (pas = `duree_minutes`)
        et retire ceux déjà réservés.
        """
        creneaux: list[datetime] = []
        actuel = datetime(day.year, day.month, day.day, start_hour, 0)
        fin = datetime(day.year, day.month, day.day, end_hour, 0)
        pas = timedelta(minutes=duree_minutes)

        # Normalise les créneaux réservés (sans secondes ni microsecondes)
        reserves_normalises = {
            dt.replace(tzinfo=None, second=0, microsecond=0) for dt in booked_slots
        }

        while actuel < fin:
            if actuel.replace(second=0, microsecond=0) not in reserves_normalises:
                creneaux.append(actuel)
            actuel += pas

        return creneaux

    def is_slot_available(
        self,
        programme_le: datetime,
        booked_slots: list[datetime],
    ) -> bool:
        """Vérifie si un créneau précis est disponible."""
        cible = programme_le.replace(tzinfo=None, second=0, microsecond=0)
        reserves_normalises = {
            dt.replace(tzinfo=None, second=0, microsecond=0) for dt in booked_slots
        }
        return cible not in reserves_normalises
