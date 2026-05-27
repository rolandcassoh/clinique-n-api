"""Services domaine appointment — Python pur, sans dépendances externes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.appointment.domain.entities import Appointment


@dataclass
class CancellationResult:
    is_full_refund: bool
    refund_amount: Decimal
    policy_applied: str  # 'full' | 'partial' | 'none'


class CancellationPolicyService:
    """Évalue la politique de remboursement selon les règles clinique."""

    def evaluate(self, appointment: "Appointment", now: datetime) -> CancellationResult:
        refund_amount = appointment.calculate_refund_amount(now)
        if refund_amount == appointment.amount:
            policy = "full"
            is_full = True
        elif refund_amount > Decimal("0"):
            policy = "partial"
            is_full = False
        else:
            policy = "none"
            is_full = False
        return CancellationResult(
            is_full_refund=is_full,
            refund_amount=refund_amount,
            policy_applied=policy,
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
        duration_minutes: int = 30,
        start_hour: int = DEFAULT_START_HOUR,
        end_hour: int = DEFAULT_END_HOUR,
    ) -> list[datetime]:
        """
        Génère tous les créneaux de la journée (pas de `duration_minutes`)
        et retire ceux déjà réservés.
        """
        slots: list[datetime] = []
        current = datetime(day.year, day.month, day.day, start_hour, 0)
        end = datetime(day.year, day.month, day.day, end_hour, 0)
        step = timedelta(minutes=duration_minutes)

        # Normalise les créneaux réservés (sans secondes ni microseconds)
        booked_normalized = {
            dt.replace(tzinfo=None, second=0, microsecond=0) for dt in booked_slots
        }

        while current < end:
            if current.replace(second=0, microsecond=0) not in booked_normalized:
                slots.append(current)
            current += step

        return slots

    def is_slot_available(
        self,
        scheduled_at: datetime,
        booked_slots: list[datetime],
    ) -> bool:
        """Vérifie si un créneau précis est disponible."""
        target = scheduled_at.replace(tzinfo=None, second=0, microsecond=0)
        booked_normalized = {
            dt.replace(tzinfo=None, second=0, microsecond=0) for dt in booked_slots
        }
        return target not in booked_normalized
