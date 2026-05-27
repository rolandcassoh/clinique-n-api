"""Use cases du module appointment."""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from app.modules.appointment.domain.entities import (
    Appointment,
    AppointmentStatus,
    AppointmentTransaction,
    AppointmentType,
    PaymentStatus,
)
from app.modules.appointment.domain.exceptions import (
    AppointmentNotFoundError,
    AppointmentPermissionError,
    InvalidPaymentGatewayError,
    PaymentAlreadyProcessedError,
    SlotNotAvailableError,
)
from app.modules.appointment.domain.repositories import (
    AppointmentRepository,
    AppointmentTransactionRepository,
)
from app.modules.appointment.domain.services import (
    CancellationPolicyService,
    CancellationResult,
    SlotAvailabilityService,
)
from app.shared.schemas.pagination import PaginationParams


# ---------------------------------------------------------------------------
# Commands (data objects)
# ---------------------------------------------------------------------------


@dataclass
class BookAppointmentCommand:
    clinic_id: int
    doctor_id: int
    patient_id: int
    scheduled_at: datetime
    type: AppointmentType = AppointmentType.IN_PERSON
    payment_gateway: Optional[str] = None
    notes: Optional[str] = None
    is_followup: bool = False
    parent_appointment_id: Optional[int] = None
    # Metadata médecin injectée depuis l'extérieur (pas de repo doctor dans ce module)
    consultation_fee: Decimal = Decimal("0")
    session_duration: int = 30


# ---------------------------------------------------------------------------
# BookAppointmentUseCase
# ---------------------------------------------------------------------------


class BookAppointmentUseCase:
    def __init__(
        self,
        repo: AppointmentRepository,
        slot_service: SlotAvailabilityService,
        redis: Any,
    ) -> None:
        self._repo = repo
        self._slot_service = slot_service
        self._redis = redis

    async def execute(self, cmd: BookAppointmentCommand) -> Appointment:
        # 1. Récupérer les créneaux déjà réservés (cache Redis ou DB)
        cache_key = f"slots:{cmd.doctor_id}:{cmd.scheduled_at.date()}"
        booked_slots = await self._get_booked_slots(cmd.doctor_id, cmd.scheduled_at, cache_key)

        # 2. Vérifier disponibilité
        if not self._slot_service.is_slot_available(cmd.scheduled_at, booked_slots):
            raise SlotNotAvailableError(cmd.scheduled_at)

        # 3. Générer référence unique
        reference = f"APT-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(100000, 999999)}"

        # 4. Créer l'appointment
        appointment = Appointment(
            id=0,
            reference=reference,
            clinic_id=cmd.clinic_id,
            doctor_id=cmd.doctor_id,
            patient_id=cmd.patient_id,
            scheduled_at=cmd.scheduled_at,
            duration_minutes=cmd.session_duration,
            status=AppointmentStatus.PENDING,
            type=cmd.type,
            amount=cmd.consultation_fee,
            advance_amount=Decimal("0"),
            payment_status=PaymentStatus.PENDING,
            payment_gateway=cmd.payment_gateway,
            notes=cmd.notes,
            is_followup=cmd.is_followup,
            parent_appointment_id=cmd.parent_appointment_id,
        )
        saved = await self._repo.save(appointment)

        # 5. Invalider le cache Redis
        await self._redis.delete(cache_key)

        return saved

    async def _get_booked_slots(
        self, doctor_id: int, scheduled_at: datetime, cache_key: str
    ) -> list[datetime]:
        """Récupère les créneaux occupés depuis la DB (cache Redis désactivé en test)."""
        try:
            import json

            cached = await self._redis.get(cache_key)
            if cached:
                raw: list[str] = json.loads(cached)
                return [datetime.fromisoformat(s) for s in raw]
        except Exception:
            pass

        booked = await self._repo.get_booked_slots(doctor_id, scheduled_at.date())
        return booked


# ---------------------------------------------------------------------------
# CancelAppointmentUseCase
# ---------------------------------------------------------------------------


class CancelAppointmentUseCase:
    def __init__(
        self,
        repo: AppointmentRepository,
        redis: Any,
    ) -> None:
        self._repo = repo
        self._redis = redis
        self._policy = CancellationPolicyService()

    async def execute(
        self, appointment_id: int, user_id: int, reason: str, is_admin: bool = False
    ) -> CancellationResult:
        appointment = await self._repo.find_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError(appointment_id)

        # Vérifier ownership (patient annule son propre RDV) sauf admin
        if not is_admin and appointment.patient_id != user_id:
            raise AppointmentPermissionError(
                "Vous ne pouvez pas annuler le rendez-vous d'un autre patient."
            )

        now = datetime.utcnow()
        result = self._policy.evaluate(appointment, now)

        appointment.cancel(reason)
        await self._repo.save(appointment)

        # Invalider cache slots
        await self._redis.delete(
            f"slots:{appointment.doctor_id}:{appointment.scheduled_at.date()}"
        )

        return result


# ---------------------------------------------------------------------------
# ConfirmAppointmentUseCase
# ---------------------------------------------------------------------------


class ConfirmAppointmentUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(self, appointment_id: int, doctor_id: int) -> Appointment:
        appointment = await self._repo.find_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError(appointment_id)
        if appointment.doctor_id != doctor_id:
            raise AppointmentPermissionError(
                "Ce rendez-vous n'appartient pas à ce médecin."
            )
        appointment.confirm()
        return await self._repo.save(appointment)


# ---------------------------------------------------------------------------
# CompleteAppointmentUseCase
# ---------------------------------------------------------------------------


class CompleteAppointmentUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(self, appointment_id: int, doctor_id: int) -> Appointment:
        appointment = await self._repo.find_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError(appointment_id)
        if appointment.doctor_id != doctor_id:
            raise AppointmentPermissionError(
                "Ce rendez-vous n'appartient pas à ce médecin."
            )
        appointment.complete()
        return await self._repo.save(appointment)


# ---------------------------------------------------------------------------
# MarkNoShowUseCase
# ---------------------------------------------------------------------------


class MarkNoShowUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(self, appointment_id: int, doctor_id: int) -> Appointment:
        appointment = await self._repo.find_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError(appointment_id)
        if appointment.doctor_id != doctor_id:
            raise AppointmentPermissionError(
                "Ce rendez-vous n'appartient pas à ce médecin."
            )
        appointment.mark_no_show()
        return await self._repo.save(appointment)


# ---------------------------------------------------------------------------
# PayAppointmentUseCase
# ---------------------------------------------------------------------------


class PayAppointmentUseCase:
    def __init__(
        self,
        repo: AppointmentRepository,
        tx_repo: AppointmentTransactionRepository,
        payment_adapter: Any,
    ) -> None:
        self._repo = repo
        self._tx_repo = tx_repo
        self._payment = payment_adapter

    async def execute(
        self,
        appointment_id: int,
        patient_id: int,
        gateway: str,
        currency: str = "XAF",
    ) -> dict:
        appointment = await self._repo.find_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError(appointment_id)
        if appointment.patient_id != patient_id:
            raise AppointmentPermissionError()
        if appointment.payment_status == PaymentStatus.PAID:
            raise PaymentAlreadyProcessedError(appointment_id)

        # Paiement wallet : stub direct
        if gateway == "wallet":
            appointment.payment_status = PaymentStatus.PAID
            appointment.payment_gateway = "wallet"
            await self._repo.save(appointment)
            await self._tx_repo.create(
                appointment_id=appointment_id,
                amount=appointment.amount,
                currency=currency,
                gateway="wallet",
                transaction_ref=f"WALLET-{appointment_id}",
                status="succeeded",
            )
            return {"status": "paid", "gateway": "wallet"}

        # Paiement via passerelle externe
        intent = await self._payment.create_payment_intent(
            amount=appointment.amount,
            currency=currency,
            metadata={"appointment_id": str(appointment_id), "reference": appointment.reference},
        )
        appointment.payment_gateway = gateway
        await self._repo.save(appointment)

        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "gateway": gateway,
        }


# ---------------------------------------------------------------------------
# CreateStripeIntentUseCase
# ---------------------------------------------------------------------------


class CreateStripeIntentUseCase:
    def __init__(
        self,
        repo: AppointmentRepository,
        stripe_adapter: Any,
    ) -> None:
        self._repo = repo
        self._stripe = stripe_adapter

    async def execute(
        self,
        appointment_id: int,
        patient_id: int,
        currency: str = "XAF",
    ) -> dict:
        appointment = await self._repo.find_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError(appointment_id)
        if appointment.patient_id != patient_id:
            raise AppointmentPermissionError()

        intent = await self._stripe.create_payment_intent(
            amount=appointment.amount,
            currency=currency,
            metadata={
                "appointment_id": str(appointment_id),
                "reference": appointment.reference,
            },
        )
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
        }


# ---------------------------------------------------------------------------
# CreateRazorpayOrderUseCase
# ---------------------------------------------------------------------------


class CreateRazorpayOrderUseCase:
    def __init__(
        self,
        repo: AppointmentRepository,
        razorpay_adapter: Any,
    ) -> None:
        self._repo = repo
        self._razorpay = razorpay_adapter

    async def execute(
        self,
        appointment_id: int,
        patient_id: int,
        currency: str = "INR",
    ) -> dict:
        appointment = await self._repo.find_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError(appointment_id)
        if appointment.patient_id != patient_id:
            raise AppointmentPermissionError()

        intent = await self._razorpay.create_payment_intent(
            amount=appointment.amount,
            currency=currency,
            metadata={"appointment_id": str(appointment_id)},
        )
        return {
            "order_id": intent.id,
            "amount": str(appointment.amount),
            "currency": currency,
        }


# ---------------------------------------------------------------------------
# RefundAppointmentUseCase
# ---------------------------------------------------------------------------


class RefundAppointmentUseCase:
    def __init__(
        self,
        repo: AppointmentRepository,
        tx_repo: AppointmentTransactionRepository,
        payment_adapter: Any,
    ) -> None:
        self._repo = repo
        self._tx_repo = tx_repo
        self._payment = payment_adapter

    async def execute(
        self,
        appointment_id: int,
        amount: Optional[Decimal] = None,
    ) -> dict:
        appointment = await self._repo.find_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError(appointment_id)

        refund_amount = amount or appointment.amount
        payment_ref = appointment.payment_reference or f"ref_{appointment_id}"

        result = await self._payment.refund(
            payment_intent_id=payment_ref, amount=refund_amount
        )
        appointment.payment_status = PaymentStatus.REFUNDED
        await self._repo.save(appointment)

        await self._tx_repo.create(
            appointment_id=appointment_id,
            amount=refund_amount,
            currency="XAF",
            gateway=appointment.payment_gateway or "unknown",
            transaction_ref=result.id,
            status="refunded",
        )
        return {"refund_id": result.id, "amount": str(refund_amount), "status": result.status}


# ---------------------------------------------------------------------------
# GetPaymentStatusUseCase
# ---------------------------------------------------------------------------


class GetPaymentStatusUseCase:
    def __init__(
        self,
        repo: AppointmentRepository,
        tx_repo: AppointmentTransactionRepository,
    ) -> None:
        self._repo = repo
        self._tx_repo = tx_repo

    async def execute(self, appointment_id: int, user_id: int) -> dict:
        appointment = await self._repo.find_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError(appointment_id)
        if appointment.patient_id != user_id:
            raise AppointmentPermissionError()

        transactions = await self._tx_repo.list_for_appointment(appointment_id)
        return {
            "appointment_id": appointment_id,
            "payment_status": appointment.payment_status,
            "payment_gateway": appointment.payment_gateway,
            "amount": str(appointment.amount),
            "transactions": [
                {
                    "ref": tx.transaction_ref,
                    "amount": str(tx.amount),
                    "status": tx.status,
                    "gateway": tx.gateway,
                }
                for tx in transactions
            ],
        }


# ---------------------------------------------------------------------------
# ForceStatusUseCase (admin)
# ---------------------------------------------------------------------------


class ForceStatusUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(self, appointment_id: int, new_status: str) -> Appointment:
        appointment = await self._repo.find_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError(appointment_id)
        appointment.status = AppointmentStatus(new_status)
        return await self._repo.save(appointment)


# ---------------------------------------------------------------------------
# GetStatsUseCase (admin)
# ---------------------------------------------------------------------------


class GetStatsUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        clinic_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> dict:
        by_status = await self._repo.count_by_status(clinic_id=clinic_id)
        revenue = await self._repo.sum_revenue(
            clinic_id=clinic_id, date_from=date_from, date_to=date_to
        )
        return {
            "by_status": by_status,
            "total_revenue": str(revenue),
        }
