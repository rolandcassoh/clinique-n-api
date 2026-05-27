"""Tests unitaires des métriques Prometheus et du HealthReport."""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Métriques Prometheus
# ---------------------------------------------------------------------------

class TestPrometheusMetrics:
    """Tests des helpers de métriques métier."""

    def test_record_appointment_created_increments_counter(self):
        """record_appointment_created() incrémente le counter avec les bons labels."""
        from app.core.monitoring.metrics import (
            record_appointment_created,
            appointments_created_total,
        )

        before = appointments_created_total.labels(
            clinic_id="clinic_1",
            payment_gateway="stripe",
            appointment_type="in_person",
        )._value.get()

        record_appointment_created("clinic_1", "stripe", "in_person")

        after = appointments_created_total.labels(
            clinic_id="clinic_1",
            payment_gateway="stripe",
            appointment_type="in_person",
        )._value.get()

        assert after == before + 1

    def test_record_appointment_created_default_type(self):
        """record_appointment_created() utilise 'in_person' comme type par défaut."""
        from app.core.monitoring.metrics import (
            record_appointment_created,
            appointments_created_total,
        )

        before = appointments_created_total.labels(
            clinic_id="clinic_default",
            payment_gateway="paystack",
            appointment_type="in_person",
        )._value.get()

        record_appointment_created("clinic_default", "paystack")

        after = appointments_created_total.labels(
            clinic_id="clinic_default",
            payment_gateway="paystack",
            appointment_type="in_person",
        )._value.get()

        assert after == before + 1

    def test_record_payment_succeeded_increments_counter(self):
        """record_payment() incrémente le counter paiements avec gateway=stripe status=succeeded."""
        from app.core.monitoring.metrics import (
            record_payment,
            payments_processed_total,
        )

        before = payments_processed_total.labels(
            gateway="stripe", status="succeeded"
        )._value.get()

        record_payment("stripe", "succeeded", amount=15000.0)

        after = payments_processed_total.labels(
            gateway="stripe", status="succeeded"
        )._value.get()

        assert after == before + 1

    def test_record_payment_increments_amount_counter(self):
        """record_payment() avec amount > 0 incrémente le compteur de montant."""
        from app.core.monitoring.metrics import (
            record_payment,
            payment_amount_total,
        )

        before = payment_amount_total.labels(gateway="flutterwave")._value.get()

        record_payment("flutterwave", "succeeded", amount=25000.0)

        after = payment_amount_total.labels(gateway="flutterwave")._value.get()

        assert after == before + 25000.0

    def test_record_payment_zero_amount_does_not_increment_amount_counter(self):
        """record_payment() avec amount=0 n'incrémente pas le compteur de montant."""
        from app.core.monitoring.metrics import (
            record_payment,
            payment_amount_total,
        )

        before = payment_amount_total.labels(gateway="razorpay")._value.get()
        record_payment("razorpay", "failed", amount=0.0)
        after = payment_amount_total.labels(gateway="razorpay")._value.get()

        assert after == before

    def test_record_slot_query_cache_hit_true(self):
        """record_slot_query(cache_hit=True) incrémente le counter avec label 'true'."""
        from app.core.monitoring.metrics import (
            record_slot_query,
            slots_queried_total,
        )

        before = slots_queried_total.labels(cache_hit="true")._value.get()
        record_slot_query(cache_hit=True)
        after = slots_queried_total.labels(cache_hit="true")._value.get()

        assert after == before + 1

    def test_record_slot_query_cache_hit_false(self):
        """record_slot_query(cache_hit=False) incrémente le counter avec label 'false'."""
        from app.core.monitoring.metrics import (
            record_slot_query,
            slots_queried_total,
        )

        before = slots_queried_total.labels(cache_hit="false")._value.get()
        record_slot_query(cache_hit=False)
        after = slots_queried_total.labels(cache_hit="false")._value.get()

        assert after == before + 1

    def test_record_notification_success(self):
        """record_notification() avec success=True incrémente le label 'success'."""
        from app.core.monitoring.metrics import (
            record_notification,
            notifications_sent_total,
        )

        before = notifications_sent_total.labels(channel="email", status="success")._value.get()
        record_notification("email", success=True)
        after = notifications_sent_total.labels(channel="email", status="success")._value.get()

        assert after == before + 1

    def test_record_notification_failed(self):
        """record_notification() avec success=False incrémente le label 'failed'."""
        from app.core.monitoring.metrics import (
            record_notification,
            notifications_sent_total,
        )

        before = notifications_sent_total.labels(channel="firebase", status="failed")._value.get()
        record_notification("firebase", success=False)
        after = notifications_sent_total.labels(channel="firebase", status="failed")._value.get()

        assert after == before + 1

    def test_record_login_attempt_success(self):
        """record_login_attempt() incrémente le counter avec status='success'."""
        from app.core.monitoring.metrics import (
            record_login_attempt,
            login_attempts_total,
        )

        before = login_attempts_total.labels(status="success")._value.get()
        record_login_attempt("success")
        after = login_attempts_total.labels(status="success")._value.get()

        assert after == before + 1

    def test_record_appointment_cancelled(self):
        """record_appointment_cancelled() incrémente le counter annulations."""
        from app.core.monitoring.metrics import (
            record_appointment_cancelled,
            appointments_cancelled_total,
        )

        before = appointments_cancelled_total.labels(
            clinic_id="clinic_99", cancellation_policy="full"
        )._value.get()

        record_appointment_cancelled("clinic_99", "full")

        after = appointments_cancelled_total.labels(
            clinic_id="clinic_99", cancellation_policy="full"
        )._value.get()

        assert after == before + 1


# ---------------------------------------------------------------------------
# HealthReport
# ---------------------------------------------------------------------------

class TestHealthReport:
    """Tests du dataclass HealthReport."""

    def test_is_healthy_true_when_status_healthy(self):
        """HealthReport.is_healthy retourne True quand status='healthy'."""
        from app.core.health.checker import HealthReport

        report = HealthReport(
            status="healthy",
            timestamp="2026-05-26T10:00:00+00:00",
            version="2.0.0",
        )
        assert report.is_healthy is True

    def test_is_healthy_false_when_status_degraded(self):
        """HealthReport.is_healthy retourne False quand status='degraded'."""
        from app.core.health.checker import HealthReport

        report = HealthReport(
            status="degraded",
            timestamp="2026-05-26T10:00:00+00:00",
            version="2.0.0",
        )
        assert report.is_healthy is False

    def test_is_healthy_false_when_status_unhealthy(self):
        """HealthReport.is_healthy retourne False quand status='unhealthy'."""
        from app.core.health.checker import HealthReport

        report = HealthReport(
            status="unhealthy",
            timestamp="2026-05-26T10:00:00+00:00",
            version="2.0.0",
        )
        assert report.is_healthy is False

    def test_to_dict_contains_all_fields(self):
        """to_dict() retourne un dictionnaire avec tous les champs attendus."""
        from app.core.health.checker import HealthReport, ServiceHealth

        report = HealthReport(
            status="healthy",
            timestamp="2026-05-26T10:00:00+00:00",
            version="2.0.0",
            services=[
                ServiceHealth("database", "healthy", 12.5),
                ServiceHealth("redis", "healthy", 3.2),
            ],
        )
        d = report.to_dict()
        assert d["status"] == "healthy"
        assert d["version"] == "2.0.0"
        assert len(d["services"]) == 2
        assert d["services"][0]["name"] == "database"
        assert d["services"][0]["latency_ms"] == 12.5

    def test_services_default_empty_list(self):
        """HealthReport sans services a une liste vide par défaut."""
        from app.core.health.checker import HealthReport

        report = HealthReport(
            status="healthy",
            timestamp="2026-05-26T10:00:00+00:00",
            version="2.0.0",
        )
        assert report.services == []

    def test_service_health_dataclass_fields(self):
        """ServiceHealth stocke correctement ses attributs."""
        from app.core.health.checker import ServiceHealth

        sh = ServiceHealth("redis", "degraded", 45.2, {"error": "timeout"})
        assert sh.name == "redis"
        assert sh.status == "degraded"
        assert sh.latency_ms == 45.2
        assert sh.details == {"error": "timeout"}


# ---------------------------------------------------------------------------
# get_health_report — tests avec mocks
# ---------------------------------------------------------------------------

class TestGetHealthReport:
    """Tests de la fonction get_health_report() avec des dépendances mockées."""

    @pytest.mark.asyncio
    async def test_get_health_report_all_healthy(self):
        """Quand tous les services sont healthy, le status global est 'healthy'."""
        from app.core.health import checker
        from app.core.health.checker import ServiceHealth, get_health_report
        from unittest.mock import AsyncMock, patch

        with patch.object(checker, "check_database", AsyncMock(
            return_value=ServiceHealth("database", "healthy", 5.0)
        )):
            with patch.object(checker, "check_redis", AsyncMock(
                return_value=ServiceHealth("redis", "healthy", 2.0)
            )):
                with patch.object(checker, "check_meilisearch", AsyncMock(
                    return_value=ServiceHealth("meilisearch", "healthy", 8.0)
                )):
                    report = await get_health_report()
                    assert report.status == "healthy"
                    assert report.is_healthy is True
                    assert len(report.services) == 3

    @pytest.mark.asyncio
    async def test_get_health_report_database_unhealthy_returns_unhealthy(self):
        """Quand la DB est unhealthy, le status global est 'unhealthy' (critique)."""
        from app.core.health import checker
        from app.core.health.checker import ServiceHealth, get_health_report
        from unittest.mock import AsyncMock, patch

        with patch.object(checker, "check_database", AsyncMock(
            return_value=ServiceHealth("database", "unhealthy", 0.0, {"error": "Connection refused"})
        )):
            with patch.object(checker, "check_redis", AsyncMock(
                return_value=ServiceHealth("redis", "healthy", 2.0)
            )):
                with patch.object(checker, "check_meilisearch", AsyncMock(
                    return_value=ServiceHealth("meilisearch", "healthy", 8.0)
                )):
                    report = await get_health_report()
                    assert report.status == "unhealthy"
                    assert report.is_healthy is False

    @pytest.mark.asyncio
    async def test_get_health_report_redis_degraded_returns_degraded(self):
        """Quand Redis est degraded (non-critique), le status global est 'degraded'."""
        from app.core.health import checker
        from app.core.health.checker import ServiceHealth, get_health_report
        from unittest.mock import AsyncMock, patch

        with patch.object(checker, "check_database", AsyncMock(
            return_value=ServiceHealth("database", "healthy", 5.0)
        )):
            with patch.object(checker, "check_redis", AsyncMock(
                return_value=ServiceHealth("redis", "degraded", 500.0, {"error": "timeout"})
            )):
                with patch.object(checker, "check_meilisearch", AsyncMock(
                    return_value=ServiceHealth("meilisearch", "healthy", 8.0)
                )):
                    report = await get_health_report()
                    assert report.status == "degraded"
                    assert report.is_healthy is False

    @pytest.mark.asyncio
    async def test_get_health_report_has_timestamp_and_version(self):
        """Le HealthReport contient un timestamp ISO et la version."""
        from app.core.health import checker
        from app.core.health.checker import ServiceHealth, get_health_report
        from unittest.mock import AsyncMock, patch

        with patch.object(checker, "check_database", AsyncMock(
            return_value=ServiceHealth("database", "healthy", 5.0)
        )):
            with patch.object(checker, "check_redis", AsyncMock(
                return_value=ServiceHealth("redis", "healthy", 2.0)
            )):
                with patch.object(checker, "check_meilisearch", AsyncMock(
                    return_value=ServiceHealth("meilisearch", "healthy", 8.0)
                )):
                    report = await get_health_report()
                    assert report.version == "2.0.0"
                    assert "T" in report.timestamp  # format ISO 8601
                    assert "+00:00" in report.timestamp or "Z" in report.timestamp
