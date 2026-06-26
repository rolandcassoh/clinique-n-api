"""Tâches Celery asynchrones pour le module rendez-vous."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _get_celery_app():
    """Initialise l'application Celery de manière paresseuse pour éviter les imports circulaires."""
    try:
        from celery import Celery
        from app.config import settings

        application_celery = Celery(
            "gestion_clinique",
            broker=settings.celery_broker_url,
            backend=getattr(settings, "celery_result_backend", settings.celery_broker_url),
        )
        application_celery.conf.update(
            task_serializer="json",
            result_serializer="json",
            accept_content=["json"],
            timezone="Africa/Douala",
            task_acks_late=True,
            task_reject_on_worker_lost=True,
        )
        return application_celery
    except Exception as exc:
        logger.warning("celery.initialisation_echouee", extra={"error": str(exc)})
        return None


_celery_app = _get_celery_app()


def _make_task(func):
    """Décorateur qui enregistre une tâche Celery si disponible, sinon crée un stub de remplacement."""
    if _celery_app is not None:
        return _celery_app.task(bind=True, max_retries=3, default_retry_delay=60)(func)
    # Stub utilisé si Celery n'est pas disponible (tests, dev sans broker)
    class _TacheStub:
        def delay(self, *args, **kwargs):
            logger.debug("celery.tache_stub", extra={"args": args, "kwargs": kwargs})
        def apply_async(self, *args, **kwargs):
            self.delay(*args, **kwargs)
    stub = _TacheStub()
    stub.__name__ = func.__name__
    return stub


# ---------------------------------------------------------------------------
# Tâche : send_appointment_notification
# ---------------------------------------------------------------------------

if _celery_app is not None:
    @_celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
    def send_appointment_notification(self, id_rendez_vous: int, event: str) -> None:
        """
        Envoie un courriel + une notification push pour un événement de rendez-vous.

        Args:
            id_rendez_vous: Identifiant du rendez-vous.
            event: Type d'événement ('created' | 'confirmed' | 'cancelled' | 'reminder').
        """
        try:
            logger.info(
                "tache.envoi_notification_rdv",
                extra={"id_rendez_vous": id_rendez_vous, "event": event},
            )
            # TODO: implémenter avec asyncio.run() vers les services de notification
            # asyncio.run(_send_notification_async(id_rendez_vous, event))
        except Exception as exc:
            logger.error(
                "tache.notification_echouee",
                extra={"id_rendez_vous": id_rendez_vous, "event": event, "error": str(exc)},
            )
            raise self.retry(exc=exc)

else:
    class send_appointment_notification:  # type: ignore[no-redef]
        @staticmethod
        def delay(id_rendez_vous: int, event: str) -> None:
            logger.debug(
                "celery.stub_notification",
                extra={"id_rendez_vous": id_rendez_vous, "event": event},
            )

        @staticmethod
        def apply_async(args=None, kwargs=None, **options) -> None:
            send_appointment_notification.delay(*(args or []), **(kwargs or {}))


# ---------------------------------------------------------------------------
# Tâche : process_payment_webhook
# ---------------------------------------------------------------------------

if _celery_app is not None:
    @_celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
    def process_payment_webhook(self, passerelle: str, event: dict) -> None:
        """
        Traitement asynchrone d'un webhook de paiement.

        Args:
            passerelle: 'stripe' | 'razorpay' | 'paypal'.
            event: Corps de l'événement webhook parsé.
        """
        try:
            logger.info(
                "tache.traitement_webhook_paiement",
                extra={"passerelle": passerelle, "event_type": event.get("type") or event.get("event")},
            )
            # TODO: router vers le gestionnaire approprié via asyncio.run()
            # asyncio.run(_handle_webhook_async(passerelle, event))
        except Exception as exc:
            logger.error(
                "tache.webhook_echoue",
                extra={"passerelle": passerelle, "error": str(exc)},
            )
            raise self.retry(exc=exc)

else:
    class process_payment_webhook:  # type: ignore[no-redef]
        @staticmethod
        def delay(passerelle: str, event: dict) -> None:
            logger.debug(
                "celery.stub_webhook",
                extra={"passerelle": passerelle},
            )

        @staticmethod
        def apply_async(args=None, kwargs=None, **options) -> None:
            process_payment_webhook.delay(*(args or []), **(kwargs or {}))


# ---------------------------------------------------------------------------
# Tâche : process_refund
# ---------------------------------------------------------------------------

if _celery_app is not None:
    @_celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
    def process_refund(self, id_rendez_vous: int, montant: float) -> None:
        """
        Lance le remboursement via la passerelle de paiement.

        Args:
            id_rendez_vous: Identifiant du rendez-vous à rembourser.
            montant: Montant du remboursement (float pour sérialisation JSON).
        """
        try:
            from decimal import Decimal

            logger.info(
                "tache.traitement_remboursement",
                extra={"id_rendez_vous": id_rendez_vous, "montant": montant},
            )
            # TODO: asyncio.run(_do_refund_async(id_rendez_vous, Decimal(str(montant))))
        except Exception as exc:
            logger.error(
                "tache.remboursement_echoue",
                extra={"id_rendez_vous": id_rendez_vous, "error": str(exc)},
            )
            raise self.retry(exc=exc)

else:
    class process_refund:  # type: ignore[no-redef]
        @staticmethod
        def delay(id_rendez_vous: int, montant: float) -> None:
            logger.debug(
                "celery.stub_remboursement",
                extra={"id_rendez_vous": id_rendez_vous, "montant": montant},
            )

        @staticmethod
        def apply_async(args=None, kwargs=None, **options) -> None:
            process_refund.delay(*(args or []), **(kwargs or {}))
