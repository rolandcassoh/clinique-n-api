from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, Summary

# ─── Rendez-vous ────────────────────────────────────────────────────────────

appointments_created_total = Counter(
    "appointments_created_total",
    "Total rendez-vous créés",
    ["id_clinique", "passerelle_paiement", "appointment_type"],
)

appointments_cancelled_total = Counter(
    "appointments_cancelled_total",
    "Total rendez-vous annulés",
    ["id_clinique", "cancellation_policy"],  # full | partial | none
)

appointments_completed_total = Counter(
    "appointments_completed_total",
    "Total rendez-vous complétés",
    ["id_clinique"],
)

appointment_booking_duration_seconds = Histogram(
    "appointment_booking_duration_seconds",
    "Temps de traitement d'une réservation (création + paiement)",
    ["passerelle_paiement"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ─── Paiements ──────────────────────────────────────────────────────────────

payments_processed_total = Counter(
    "payments_processed_total",
    "Total paiements traités",
    ["passerelle", "statut"],  # succeeded | failed | refunded
)

payment_amount_total = Counter(
    "payment_amount_total_xaf",
    "Montant total traité (en XAF)",
    ["passerelle"],
)

payment_processing_seconds = Histogram(
    "payment_processing_seconds",
    "Temps de traitement d'un paiement",
    ["passerelle"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
)

# ─── Clinique ────────────────────────────────────────────────────────────────

active_doctors_gauge = Gauge(
    "active_doctors_total",
    "Nombre de médecins actifs",
    ["id_clinique"],
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
    ["channel", "statut"],  # channel: courriel|firebase|onesignal, statut: success|failed
)

# ─── Auth ────────────────────────────────────────────────────────────────────

login_attempts_total = Counter(
    "login_attempts_total",
    "Tentatives de connexion",
    ["statut"],  # success | failed | blocked
)

# ─── Helpers ─────────────────────────────────────────────────────────────────


def record_appointment_created(
    id_clinique: str, passerelle: str, apt_type: str = "in_person"
) -> None:
    """Incrémente le compteur de rendez-vous créés."""
    appointments_created_total.labels(
        id_clinique=id_clinique,
        passerelle_paiement=passerelle,
        appointment_type=apt_type,
    ).inc()


def record_appointment_cancelled(
    id_clinique: str, cancellation_policy: str = "none"
) -> None:
    """Incrémente le compteur de rendez-vous annulés."""
    appointments_cancelled_total.labels(
        id_clinique=id_clinique,
        cancellation_policy=cancellation_policy,
    ).inc()


def record_appointment_completed(id_clinique: str) -> None:
    """Incrémente le compteur de rendez-vous complétés."""
    appointments_completed_total.labels(id_clinique=id_clinique).inc()


def record_payment(passerelle: str, statut: str, montant: float = 0.0) -> None:
    """Enregistre un paiement traité."""
    payments_processed_total.labels(passerelle=passerelle, statut=statut).inc()
    if montant > 0:
        payment_amount_total.labels(passerelle=passerelle).inc(montant)


def record_slot_query(cache_hit: bool) -> None:
    """Enregistre une requête de disponibilités."""
    slots_queried_total.labels(cache_hit=str(cache_hit).lower()).inc()


def record_notification(channel: str, success: bool) -> None:
    """Enregistre l'envoi d'une notification."""
    notifications_sent_total.labels(
        channel=channel,
        statut="success" if success else "failed",
    ).inc()


def record_login_attempt(statut: str) -> None:
    """Enregistre une tentative de connexion (success | failed | blocked)."""
    login_attempts_total.labels(statut=statut).inc()
