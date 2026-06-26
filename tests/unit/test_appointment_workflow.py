"""Tests unitaires des workflows appointment (services domaine + use cases avec mocks)."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from app.modules.rendez_vous.domain.entites import (
    Appointment,
    AppointmentStatus,
    AppointmentType,
    PaymentStatus,
)
from app.modules.rendez_vous.domain.exceptions import SlotNotAvailableError
from app.modules.rendez_vous.domain.services import (
    CancellationPolicyService,
    SlotAvailabilityService,
)
from app.modules.rendez_vous.application.cas_utilisation import (
    BookAppointmentCommand,
    BookAppointmentUseCase,
    CancelAppointmentUseCase,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_appointment(
    status: AppointmentStatus = AppointmentStatus.PENDING,
    scheduled_at: datetime | None = None,
    amount: Decimal = Decimal("10000"),
    patient_id: int = 42,
    doctor_id: int = 10,
    appointment_id: int = 1,
) -> Appointment:
    return Appointment(
        id=appointment_id,
        reference="APT-20240101-123456",
        clinic_id=1,
        doctor_id=doctor_id,
        patient_id=patient_id,
        scheduled_at=scheduled_at or datetime.utcnow() + timedelta(hours=48),
        duration_minutes=30,
        status=status,
        type=AppointmentType.IN_PERSON,
        amount=amount,
        advance_amount=Decimal("0"),
        payment_status=PaymentStatus.PENDING,
    )


# ---------------------------------------------------------------------------
# CancellationPolicyService
# ---------------------------------------------------------------------------


class TestCancellationPolicyService:
    def _policy(self) -> CancellationPolicyService:
        return CancellationPolicyService()

    def test_full_refund_more_than_24h(self):
        policy = self._policy()
        now = datetime(2024, 6, 1, 10, 0)
        apt = _make_appointment(scheduled_at=datetime(2024, 6, 3, 10, 0), amount=Decimal("20000"))
        result = policy.evaluate(apt, now)
        assert result.is_full_refund is True
        assert result.refund_amount == Decimal("20000")
        assert result.policy_applied == "full"

    def test_partial_refund_6_to_24h(self):
        policy = self._policy()
        now = datetime(2024, 6, 1, 8, 0)
        # 12 heures plus tard
        apt = _make_appointment(scheduled_at=datetime(2024, 6, 1, 20, 0), amount=Decimal("10000"))
        result = policy.evaluate(apt, now)
        assert result.is_full_refund is False
        assert result.refund_amount == Decimal("5000")
        assert result.policy_applied == "partial"

    def test_no_refund_less_than_6h(self):
        policy = self._policy()
        now = datetime(2024, 6, 1, 10, 0)
        # 3 heures plus tard
        apt = _make_appointment(scheduled_at=datetime(2024, 6, 1, 13, 0), amount=Decimal("10000"))
        result = policy.evaluate(apt, now)
        assert result.is_full_refund is False
        assert result.refund_amount == Decimal("0")
        assert result.policy_applied == "none"

    def test_partial_refund_decimal_precision(self):
        """Vérifie que la division 50% est précise sur des montants impairs."""
        policy = self._policy()
        now = datetime(2024, 6, 1, 8, 0)
        apt = _make_appointment(scheduled_at=datetime(2024, 6, 1, 20, 0), amount=Decimal("999"))
        result = policy.evaluate(apt, now)
        assert result.refund_amount == Decimal("999") * Decimal("0.5")


# ---------------------------------------------------------------------------
# SlotAvailabilityService
# ---------------------------------------------------------------------------


class TestSlotAvailabilityService:
    def test_slot_available_when_no_bookings(self):
        svc = SlotAvailabilityService()
        day = datetime(2024, 6, 3).date()
        slots = svc.get_available_slots(day, booked_slots=[], duration_minutes=30)
        assert len(slots) > 0  # 8h-18h = 20 créneaux de 30min

    def test_slot_not_available_when_booked(self):
        svc = SlotAvailabilityService()
        booked = datetime(2024, 6, 3, 9, 0)
        available = svc.is_slot_available(
            datetime(2024, 6, 3, 9, 0), booked_slots=[booked]
        )
        assert available is False

    def test_slot_available_when_different_time(self):
        svc = SlotAvailabilityService()
        booked = datetime(2024, 6, 3, 9, 0)
        available = svc.is_slot_available(
            datetime(2024, 6, 3, 9, 30), booked_slots=[booked]
        )
        assert available is True

    def test_generates_correct_number_of_slots(self):
        svc = SlotAvailabilityService()
        day = datetime(2024, 6, 3).date()
        # 8h-18h = 10 heures = 20 créneaux de 30min
        slots = svc.get_available_slots(
            day, booked_slots=[], duration_minutes=30,
            start_hour=8, end_hour=18
        )
        assert len(slots) == 20

    def test_available_slots_excludes_booked(self):
        svc = SlotAvailabilityService()
        day = datetime(2024, 6, 3).date()
        booked = [datetime(2024, 6, 3, 8, 0), datetime(2024, 6, 3, 9, 0)]
        slots = svc.get_available_slots(day, booked_slots=booked, duration_minutes=30)
        assert len(slots) == 18  # 20 - 2


# ---------------------------------------------------------------------------
# BookAppointmentUseCase (avec repo mock)
# ---------------------------------------------------------------------------


class TestBookAppointmentUseCase:
    def _make_use_case(self, booked_slots=None):
        """Crée un use case avec des dépendances mockées."""
        repo = AsyncMock()
        slot_service = SlotAvailabilityService()
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)  # Pas de cache
        redis.delete = AsyncMock(return_value=True)

        # repo.save retourne l'appointment avec un ID
        async def fake_save(apt: Appointment) -> Appointment:
            apt.id = 1
            return apt

        repo.save = fake_save
        repo.get_booked_slots = AsyncMock(return_value=booked_slots or [])

        uc = BookAppointmentUseCase(repo=repo, slot_service=slot_service, redis=redis)
        return uc, repo, redis

    @pytest.mark.asyncio
    async def test_book_available_slot_creates_appointment(self):
        uc, repo, redis = self._make_use_case(booked_slots=[])
        scheduled = datetime(2024, 6, 3, 9, 0)
        cmd = BookAppointmentCommand(
            clinic_id=1,
            doctor_id=10,
            patient_id=42,
            scheduled_at=scheduled,
            consultation_fee=Decimal("5000"),
            session_duration=30,
        )
        result = await uc.execute(cmd)
        assert result.id == 1
        assert result.reference.startswith("APT-")
        assert result.doctor_id == 10
        assert result.patient_id == 42
        assert result.status == AppointmentStatus.PENDING
        assert result.amount == Decimal("5000")

    @pytest.mark.asyncio
    async def test_book_already_booked_slot_raises(self):
        booked = [datetime(2024, 6, 3, 9, 0)]
        uc, repo, redis = self._make_use_case(booked_slots=booked)
        scheduled = datetime(2024, 6, 3, 9, 0)
        cmd = BookAppointmentCommand(
            clinic_id=1,
            doctor_id=10,
            patient_id=42,
            scheduled_at=scheduled,
            consultation_fee=Decimal("5000"),
        )
        with pytest.raises(SlotNotAvailableError):
            await uc.execute(cmd)

    @pytest.mark.asyncio
    async def test_book_invalidates_redis_cache(self):
        uc, repo, redis = self._make_use_case(booked_slots=[])
        scheduled = datetime(2024, 6, 3, 10, 0)
        cmd = BookAppointmentCommand(
            clinic_id=1,
            doctor_id=10,
            patient_id=42,
            scheduled_at=scheduled,
        )
        await uc.execute(cmd)
        redis.delete.assert_called_once_with("slots:10:2024-06-03")

    @pytest.mark.asyncio
    async def test_reference_format(self):
        uc, _, _ = self._make_use_case(booked_slots=[])
        scheduled = datetime(2024, 6, 3, 11, 0)
        cmd = BookAppointmentCommand(
            clinic_id=1, doctor_id=10, patient_id=42, scheduled_at=scheduled
        )
        result = await uc.execute(cmd)
        # Format: APT-YYYYMMDD-NNNNNN
        parts = result.reference.split("-")
        assert parts[0] == "APT"
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 6  # 6 chiffres


# ---------------------------------------------------------------------------
# CancelAppointmentUseCase (avec repo mock)
# ---------------------------------------------------------------------------


class TestCancelAppointmentUseCase:
    @pytest.mark.asyncio
    async def test_cancel_own_appointment_ok(self):
        repo = AsyncMock()
        redis = AsyncMock()
        redis.delete = AsyncMock(return_value=True)

        apt = _make_appointment(
            status=AppointmentStatus.CONFIRMED,
            scheduled_at=datetime.utcnow() + timedelta(hours=48),
            patient_id=42,
        )
        repo.find_by_id = AsyncMock(return_value=apt)
        repo.save = AsyncMock(return_value=apt)

        uc = CancelAppointmentUseCase(repo=repo, redis=redis)
        result = await uc.execute(
            appointment_id=1, user_id=42, reason="Voyage imprévu"
        )
        assert result.policy_applied in ("full", "partial", "none")
        assert apt.status == AppointmentStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_other_patient_raises(self):
        from app.modules.rendez_vous.domain.exceptions import AppointmentPermissionError

        repo = AsyncMock()
        redis = AsyncMock()

        apt = _make_appointment(patient_id=99)
        repo.find_by_id = AsyncMock(return_value=apt)

        uc = CancelAppointmentUseCase(repo=repo, redis=redis)
        with pytest.raises(AppointmentPermissionError):
            await uc.execute(appointment_id=1, user_id=42, reason="Raison")

    @pytest.mark.asyncio
    async def test_cancel_admin_bypass_ownership(self):
        repo = AsyncMock()
        redis = AsyncMock()
        redis.delete = AsyncMock(return_value=True)

        apt = _make_appointment(patient_id=99, status=AppointmentStatus.CONFIRMED)
        repo.find_by_id = AsyncMock(return_value=apt)
        repo.save = AsyncMock(return_value=apt)

        uc = CancelAppointmentUseCase(repo=repo, redis=redis)
        # is_admin=True permet de contourner le check ownership
        result = await uc.execute(
            appointment_id=1, user_id=999, reason="Admin cancel", is_admin=True
        )
        assert apt.status == AppointmentStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_not_found_raises(self):
        from app.modules.rendez_vous.domain.exceptions import AppointmentNotFoundError

        repo = AsyncMock()
        redis = AsyncMock()
        repo.find_by_id = AsyncMock(return_value=None)

        uc = CancelAppointmentUseCase(repo=repo, redis=redis)
        with pytest.raises(AppointmentNotFoundError):
            await uc.execute(appointment_id=999, user_id=42, reason="Raison")
