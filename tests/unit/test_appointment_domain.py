"""Tests unitaires des entités domaine appointment."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.modules.appointment.domain.entities import (
    Appointment,
    AppointmentStatus,
    AppointmentType,
    PaymentStatus,
)


def _make_appointment(
    status: AppointmentStatus = AppointmentStatus.PENDING,
    scheduled_at: datetime | None = None,
    amount: Decimal = Decimal("10000"),
) -> Appointment:
    return Appointment(
        id=1,
        reference="APT-20240101-123456",
        clinic_id=1,
        doctor_id=10,
        patient_id=42,
        scheduled_at=scheduled_at or datetime.utcnow() + timedelta(hours=48),
        duration_minutes=30,
        status=status,
        type=AppointmentType.IN_PERSON,
        amount=amount,
        advance_amount=Decimal("0"),
        payment_status=PaymentStatus.PENDING,
    )


# ---------------------------------------------------------------------------
# confirm()
# ---------------------------------------------------------------------------


class TestConfirm:
    def test_confirm_pending_ok(self):
        apt = _make_appointment(AppointmentStatus.PENDING)
        apt.confirm()
        assert apt.status == AppointmentStatus.CONFIRMED

    def test_confirm_already_confirmed_raises(self):
        apt = _make_appointment(AppointmentStatus.CONFIRMED)
        with pytest.raises(ValueError, match="Cannot confirm"):
            apt.confirm()

    def test_confirm_cancelled_raises(self):
        apt = _make_appointment(AppointmentStatus.CANCELLED)
        with pytest.raises(ValueError, match="Cannot confirm"):
            apt.confirm()

    def test_confirm_completed_raises(self):
        apt = _make_appointment(AppointmentStatus.COMPLETED)
        with pytest.raises(ValueError, match="Cannot confirm"):
            apt.confirm()


# ---------------------------------------------------------------------------
# complete()
# ---------------------------------------------------------------------------


class TestComplete:
    def test_complete_confirmed_ok(self):
        apt = _make_appointment(AppointmentStatus.CONFIRMED)
        apt.complete()
        assert apt.status == AppointmentStatus.COMPLETED

    def test_complete_pending_raises(self):
        apt = _make_appointment(AppointmentStatus.PENDING)
        with pytest.raises(ValueError, match="Cannot complete"):
            apt.complete()


# ---------------------------------------------------------------------------
# mark_no_show()
# ---------------------------------------------------------------------------


class TestMarkNoShow:
    def test_no_show_confirmed_ok(self):
        apt = _make_appointment(AppointmentStatus.CONFIRMED)
        apt.mark_no_show()
        assert apt.status == AppointmentStatus.NO_SHOW

    def test_no_show_pending_raises(self):
        apt = _make_appointment(AppointmentStatus.PENDING)
        with pytest.raises(ValueError, match="Cannot mark no_show"):
            apt.mark_no_show()


# ---------------------------------------------------------------------------
# cancel()
# ---------------------------------------------------------------------------


class TestCancel:
    def test_cancel_pending_ok(self):
        apt = _make_appointment(AppointmentStatus.PENDING)
        apt.cancel("Test annulation")
        assert apt.status == AppointmentStatus.CANCELLED
        assert apt.cancellation_reason == "Test annulation"

    def test_cancel_confirmed_ok(self):
        apt = _make_appointment(AppointmentStatus.CONFIRMED)
        apt.cancel("Urgence")
        assert apt.status == AppointmentStatus.CANCELLED

    def test_cancel_completed_raises(self):
        apt = _make_appointment(AppointmentStatus.COMPLETED)
        with pytest.raises(ValueError, match="Cannot cancel a completed"):
            apt.cancel("raison")

    def test_cancel_already_cancelled_raises(self):
        apt = _make_appointment(AppointmentStatus.CANCELLED)
        with pytest.raises(ValueError, match="already cancelled"):
            apt.cancel("re-annulation")


# ---------------------------------------------------------------------------
# calculate_refund_amount()
# ---------------------------------------------------------------------------


class TestCalculateRefundAmount:
    def test_more_than_24h_full_refund(self):
        now = datetime(2024, 6, 1, 10, 0)
        scheduled = datetime(2024, 6, 3, 10, 0)  # 48h plus tard
        apt = _make_appointment(
            scheduled_at=scheduled, amount=Decimal("15000")
        )
        refund = apt.calculate_refund_amount(now)
        assert refund == Decimal("15000")

    def test_exactly_24h_full_refund(self):
        now = datetime(2024, 6, 1, 10, 0)
        scheduled = datetime(2024, 6, 2, 10, 0)  # exactement 24h
        apt = _make_appointment(scheduled_at=scheduled, amount=Decimal("15000"))
        refund = apt.calculate_refund_amount(now)
        assert refund == Decimal("15000")

    def test_between_6h_and_24h_partial_refund(self):
        now = datetime(2024, 6, 1, 10, 0)
        scheduled = datetime(2024, 6, 1, 22, 0)  # 12h plus tard
        apt = _make_appointment(scheduled_at=scheduled, amount=Decimal("10000"))
        refund = apt.calculate_refund_amount(now)
        assert refund == Decimal("5000")

    def test_exactly_6h_partial_refund(self):
        now = datetime(2024, 6, 1, 10, 0)
        scheduled = datetime(2024, 6, 1, 16, 0)  # exactement 6h
        apt = _make_appointment(scheduled_at=scheduled, amount=Decimal("10000"))
        refund = apt.calculate_refund_amount(now)
        assert refund == Decimal("5000")

    def test_less_than_6h_no_refund(self):
        now = datetime(2024, 6, 1, 10, 0)
        scheduled = datetime(2024, 6, 1, 13, 0)  # 3h plus tard
        apt = _make_appointment(scheduled_at=scheduled, amount=Decimal("10000"))
        refund = apt.calculate_refund_amount(now)
        assert refund == Decimal("0")

    def test_past_appointment_no_refund(self):
        now = datetime(2024, 6, 2, 10, 0)
        scheduled = datetime(2024, 6, 1, 10, 0)  # passé
        apt = _make_appointment(scheduled_at=scheduled, amount=Decimal("10000"))
        refund = apt.calculate_refund_amount(now)
        assert refund == Decimal("0")

    def test_zero_amount_refund(self):
        now = datetime(2024, 6, 1, 10, 0)
        scheduled = datetime(2024, 6, 3, 10, 0)
        apt = _make_appointment(scheduled_at=scheduled, amount=Decimal("0"))
        refund = apt.calculate_refund_amount(now)
        assert refund == Decimal("0")


# ---------------------------------------------------------------------------
# is_cancellable_without_charge()
# ---------------------------------------------------------------------------


class TestIsCancellableWithoutCharge:
    def test_more_than_24h_free_cancel(self):
        now = datetime(2024, 6, 1, 10, 0)
        scheduled = datetime(2024, 6, 3, 10, 0)  # 48h
        apt = _make_appointment(scheduled_at=scheduled)
        assert apt.is_cancellable_without_charge(now) is True

    def test_exactly_24h_free_cancel(self):
        now = datetime(2024, 6, 1, 10, 0)
        scheduled = datetime(2024, 6, 2, 10, 0)  # 24h exactement
        apt = _make_appointment(scheduled_at=scheduled)
        assert apt.is_cancellable_without_charge(now) is True

    def test_less_than_24h_not_free(self):
        now = datetime(2024, 6, 1, 10, 0)
        scheduled = datetime(2024, 6, 1, 22, 0)  # 12h
        apt = _make_appointment(scheduled_at=scheduled)
        assert apt.is_cancellable_without_charge(now) is False

    def test_custom_policy_48h(self):
        now = datetime(2024, 6, 1, 10, 0)
        scheduled = datetime(2024, 6, 3, 10, 0)  # 48h
        apt = _make_appointment(scheduled_at=scheduled)
        assert apt.is_cancellable_without_charge(now, policy_hours=48) is True
        assert apt.is_cancellable_without_charge(now, policy_hours=72) is False
