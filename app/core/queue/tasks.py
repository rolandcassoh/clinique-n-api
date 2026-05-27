"""Tâches Celery asynchrones pour le module appointment."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _get_celery_app():
    """Initialise l'app Celery de manière lazy pour éviter les imports circulaires."""
    try:
        from celery import Celery
        from app.config import settings

        celery_app = Celery(
            "gestion_clinique",
            broker=settings.celery_broker_url,
            backend=getattr(settings, "celery_result_backend", settings.celery_broker_url),
        )
        celery_app.conf.update(
            task_serializer="json",
            result_serializer="json",
            accept_content=["json"],
            timezone="Africa/Douala",
            task_acks_late=True,
            task_reject_on_worker_lost=True,
        )
        return celery_app
    except Exception as exc:
        logger.warning("celery_init_failed", extra={"error": str(exc)})
        return None


_celery_app = _get_celery_app()


def _make_task(func):
    """Décorateur qui enregistre une tâche Celery si disponible, sinon crée un stub."""
    if _celery_app is not None:
        return _celery_app.task(bind=True, max_retries=3, default_retry_delay=60)(func)
    # Stub si Celery n'est pas disponible (tests, dev sans broker)
    class _StubTask:
        def delay(self, *args, **kwargs):
            logger.debug("celery_stub_task", extra={"args": args, "kwargs": kwargs})
        def apply_async(self, *args, **kwargs):
            self.delay(*args, **kwargs)
    stub = _StubTask()
    stub.__name__ = func.__name__
    return stub


# ---------------------------------------------------------------------------
# Tâche : send_appointment_notification
# ---------------------------------------------------------------------------

if _celery_app is not None:
    @_celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
    def send_appointment_notification(self, appointment_id: int, event: str) -> None:
        """
        Envoie email + push notification pour un événement RDV.

        Args:
            appointment_id: ID du rendez-vous.
            event: Type d'événement ('created' | 'confirmed' | 'cancelled' | 'reminder').
        """
        try:
            logger.info(
                "send_appointment_notification",
                extra={"appointment_id": appointment_id, "event": event},
            )
            # TODO: implémenter avec asyncio.run() vers les services de notification
            # asyncio.run(_send_notification_async(appointment_id, event))
        except Exception as exc:
            logger.error(
                "notification_failed",
                extra={"appointment_id": appointment_id, "event": event, "error": str(exc)},
            )
            raise self.retry(exc=exc)

else:
    class send_appointment_notification:  # type: ignore[no-redef]
        @staticmethod
        def delay(appointment_id: int, event: str) -> None:
            logger.debug(
                "celery_stub_notification",
                extra={"appointment_id": appointment_id, "event": event},
            )

        @staticmethod
        def apply_async(args=None, kwargs=None, **options) -> None:
            send_appointment_notification.delay(*(args or []), **(kwargs or {}))


# ---------------------------------------------------------------------------
# Tâche : process_payment_webhook
# ---------------------------------------------------------------------------

if _celery_app is not None:
    @_celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
    def process_payment_webhook(self, gateway: str, event: dict) -> None:
        """
        Traitement asynchrone d'un webhook paiement.

        Args:
            gateway: 'stripe' | 'razorpay' | 'paypal'.
            event: Corps de l'événement webhook parsé.
        """
        try:
            logger.info(
                "process_payment_webhook",
                extra={"gateway": gateway, "event_type": event.get("type") or event.get("event")},
            )
            # TODO: router vers le handler approprié via asyncio.run()
            # asyncio.run(_handle_webhook_async(gateway, event))
        except Exception as exc:
            logger.error(
                "webhook_processing_failed",
                extra={"gateway": gateway, "error": str(exc)},
            )
            raise self.retry(exc=exc)

else:
    class process_payment_webhook:  # type: ignore[no-redef]
        @staticmethod
        def delay(gateway: str, event: dict) -> None:
            logger.debug(
                "celery_stub_webhook",
                extra={"gateway": gateway},
            )

        @staticmethod
        def apply_async(args=None, kwargs=None, **options) -> None:
            process_payment_webhook.delay(*(args or []), **(kwargs or {}))


# ---------------------------------------------------------------------------
# Tâche : process_refund
# ---------------------------------------------------------------------------

if _celery_app is not None:
    @_celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
    def process_refund(self, appointment_id: int, amount: float) -> None:
        """
        Lance le remboursement via la passerelle de paiement.

        Args:
            appointment_id: ID du rendez-vous à rembourser.
            amount: Montant du remboursement (float pour sérialisation JSON).
        """
        try:
            from decimal import Decimal

            logger.info(
                "process_refund",
                extra={"appointment_id": appointment_id, "amount": amount},
            )
            # TODO: asyncio.run(_do_refund_async(appointment_id, Decimal(str(amount))))
        except Exception as exc:
            logger.error(
                "refund_failed",
                extra={"appointment_id": appointment_id, "error": str(exc)},
            )
            raise self.retry(exc=exc)

else:
    class process_refund:  # type: ignore[no-redef]
        @staticmethod
        def delay(appointment_id: int, amount: float) -> None:
            logger.debug(
                "celery_stub_refund",
                extra={"appointment_id": appointment_id, "amount": amount},
            )

        @staticmethod
        def apply_async(args=None, kwargs=None, **options) -> None:
            process_refund.delay(*(args or []), **(kwargs or {}))
