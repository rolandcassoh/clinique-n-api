from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, Summary

# ─── Rendez-vous ────────────────────────────────────────────────────────────

appointments_created_total = Counter(
    "appointments_created_total",
    "Total rendez-vous créés",
    ["clinic_id", "payment_gateway", "appointment_type"],
)

appointments_cancelled_total = Counter(
    "appointments_cancelled_total",
    "Total rendez-vous annulés",
    ["clinic_id", "cancellation_policy"],  # full | partial | none
)

appointments_completed_total = Counter(
    "appointments_completed_total",
    "Total rendez-vous complétés",
    ["clinic_id"],
)

appointment_booking_duration_seconds = Histogram(
    "appointment_booking_duration_seconds",
    "Temps de traitement d'une réservation (création + paiement)",
    ["payment_gateway"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ─── Paiements ──────────────────────────────────────────────────────────────

payments_processed_total = Counter(
    "payments_processed_total",
    "Total paiements traités",
    ["gateway", "status"],  # succeeded | failed | refunded
)

payment_amount_total = Counter(
    "payment_amount_total_xaf",
    "Montant total traité (en XAF)",
    ["gateway"],
)

payment_processing_seconds = Histogram(
    "payment_processing_seconds",
    "Temps de traitement d'un paiement",
    ["gateway"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
)

# ─── Clinique ────────────────────────────────────────────────────────────────

active_doctors_gauge = Gauge(
    "active_doctors_total",
    "Nombre de médecins actifs",
    ["clinic_id"],
)

slots_queried_total = Counter(
    "doctor_slots_queried_total",
    "Nombre de requêtes de disponibilités médecin",
    ["cache_hit"],  # true | false
)

# ─── Notifications ───────────────────────────────────────────────────────────

notifications_sent_total = Counter(
    "notifications_sent_total",
    "Notifications envoyées",
    ["channel", "status"],  # channel: email|firebase|onesignal, status: success|failed
)

# ─── Auth ────────────────────────────────────────────────────────────────────

login_attempts_total = Counter(
    "login_attempts_total",
    "Tentatives de connexion",
    ["status"],  # success | failed | blocked
)

# ─── Helpers ─────────────────────────────────────────────────────────────────


def record_appointment_created(
    clinic_id: str, gateway: str, apt_type: str = "in_person"
) -> None:
    """Incrémente le compteur de rendez-vous créés."""
    appointments_created_total.labels(
        clinic_id=clinic_id,
        payment_gateway=gateway,
        appointment_type=apt_type,
    ).inc()


def record_appointment_cancelled(
    clinic_id: str, cancellation_policy: str = "none"
) -> None:
    """Incrémente le compteur de rendez-vous annulés."""
    appointments_cancelled_total.labels(
        clinic_id=clinic_id,
        cancellation_policy=cancellation_policy,
    ).inc()


def record_appointment_completed(clinic_id: str) -> None:
    """Incrémente le compteur de rendez-vous complétés."""
    appointments_completed_total.labels(clinic_id=clinic_id).inc()


def record_payment(gateway: str, status: str, amount: float = 0.0) -> None:
    """Enregistre un paiement traité."""
    payments_processed_total.labels(gateway=gateway, status=status).inc()
    if amount > 0:
        payment_amount_total.labels(gateway=gateway).inc(amount)


def record_slot_query(cache_hit: bool) -> None:
    """Enregistre une requête de disponibilités."""
    slots_queried_total.labels(cache_hit=str(cache_hit).lower()).inc()


def record_notification(channel: str, success: bool) -> None:
    """Enregistre l'envoi d'une notification."""
    notifications_sent_total.labels(
        channel=channel,
        status="success" if success else "failed",
    ).inc()


def record_login_attempt(status: str) -> None:
    """Enregistre une tentative de connexion (success | failed | blocked)."""
    login_attempts_total.labels(status=status).inc()
