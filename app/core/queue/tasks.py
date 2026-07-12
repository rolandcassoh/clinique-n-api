"""Tâches Celery asynchrones pour le module rendez-vous."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Fonctions asynchrones internes
# ---------------------------------------------------------------------------

async def _send_notification_async(id_rendez_vous: int, event: str) -> None:
    """
    Envoie une notification asynchrone pour un rendez-vous.
    
    Args:
        id_rendez_vous: ID du rendez-vous
        event: Type d'événement (created, confirmed, cancelled, reminder)
    """
    date_debut = datetime.utcnow().isoformat()
    
    try:
        logger.info(
            "Début envoi notification asynchrone",
            extra={
                "date": date_debut,
                "id_rendez_vous": id_rendez_vous,
                "event": event,
            },
        )
        
        # TODO: Implémenter l'envoi réel via services de notification
        # - Email via SMTP/SendGrid
        # - Push notification via Firebase/OneSignal
        # - SMS via Twilio (optionnel)
        
        # Simulation temporaire
        await asyncio.sleep(0.1)
        
        date_fin = datetime.utcnow().isoformat()
        logger.info(
            "Notification envoyée avec succès",
            extra={
                "date_debut": date_debut,
                "date_fin": date_fin,
                "id_rendez_vous": id_rendez_vous,
                "event": event,
                "status": "success",
            },
        )
        
    except Exception as e:
        date_erreur = datetime.utcnow().isoformat()
        logger.error(
            "Erreur envoi notification asynchrone",
            extra={
                "date_debut": date_debut,
                "date_erreur": date_erreur,
                "id_rendez_vous": id_rendez_vous,
                "event": event,
                "erreur": str(e),
            },
            exc_info=True,
        )
        raise


async def _handle_webhook_async(passerelle: str, event: dict) -> None:
    """
    Traite un webhook de paiement de manière asynchrone.
    
    Args:
        passerelle: Nom de la passerelle (stripe, razorpay, paypal)
        event: Données de l'événement webhook
    """
    date_debut = datetime.utcnow().isoformat()
    event_type = event.get("type") or event.get("event")
    
    try:
        logger.info(
            "Début traitement webhook asynchrone",
            extra={
                "date": date_debut,
                "passerelle": passerelle,
                "event_type": event_type,
                "event_id": event.get("id"),
            },
        )
        
        # Router vers le gestionnaire approprié selon la passerelle
        if passerelle == "stripe":
            await _handle_stripe_webhook(event)
        elif passerelle == "razorpay":
            await _handle_razorpay_webhook(event)
        elif passerelle == "paypal":
            await _handle_paypal_webhook(event)
        else:
            logger.warning(
                "Passerelle de paiement non supportée",
                extra={
                    "date": datetime.utcnow().isoformat(),
                    "passerelle": passerelle,
                },
            )
        
        date_fin = datetime.utcnow().isoformat()
        logger.info(
            "Webhook traité avec succès",
            extra={
                "date_debut": date_debut,
                "date_fin": date_fin,
                "passerelle": passerelle,
                "event_type": event_type,
                "status": "success",
            },
        )
        
    except Exception as e:
        date_erreur = datetime.utcnow().isoformat()
        logger.error(
            "Erreur traitement webhook asynchrone",
            extra={
                "date_debut": date_debut,
                "date_erreur": date_erreur,
                "passerelle": passerelle,
                "event_type": event_type,
                "erreur": str(e),
            },
            exc_info=True,
        )
        raise


async def _handle_stripe_webhook(event: dict) -> None:
    """Traite un webhook Stripe."""
    # TODO: Implémenter la logique Stripe
    await asyncio.sleep(0.1)
    logger.debug("Webhook Stripe traité", extra={"event_type": event.get("type")})


async def _handle_razorpay_webhook(event: dict) -> None:
    """Traite un webhook Razorpay."""
    # TODO: Implémenter la logique Razorpay
    await asyncio.sleep(0.1)
    logger.debug("Webhook Razorpay traité", extra={"event": event.get("event")})


async def _handle_paypal_webhook(event: dict) -> None:
    """Traite un webhook PayPal."""
    # TODO: Implémenter la logique PayPal
    await asyncio.sleep(0.1)
    logger.debug("Webhook PayPal traité", extra={"event_type": event.get("event_type")})


async def _do_refund_async(id_rendez_vous: int, montant: Decimal) -> None:
    """
    Effectue un remboursement de manière asynchrone.
    
    Args:
        id_rendez_vous: ID du rendez-vous à rembourser
        montant: Montant à rembourser
    """
    date_debut = datetime.utcnow().isoformat()
    
    try:
        logger.info(
            "Début remboursement asynchrone",
            extra={
                "date": date_debut,
                "id_rendez_vous": id_rendez_vous,
                "montant": str(montant),
            },
        )
        
        # TODO: Implémenter l'appel réel à la passerelle de paiement
        # - Récupérer les infos de transaction depuis la DB
        # - Appeler l'API de remboursement (Stripe/Razorpay/PayPal)
        # - Mettre à jour le statut de la transaction
        
        # Simulation temporaire
        await asyncio.sleep(0.1)
        
        date_fin = datetime.utcnow().isoformat()
        logger.info(
            "Remboursement effectué avec succès",
            extra={
                "date_debut": date_debut,
                "date_fin": date_fin,
                "id_rendez_vous": id_rendez_vous,
                "montant": str(montant),
                "status": "success",
            },
        )
        
    except Exception as e:
        date_erreur = datetime.utcnow().isoformat()
        logger.error(
            "Erreur remboursement asynchrone",
            extra={
                "date_debut": date_debut,
                "date_erreur": date_erreur,
                "id_rendez_vous": id_rendez_vous,
                "montant": str(montant),
                "erreur": str(e),
            },
            exc_info=True,
        )
        raise


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
            asyncio.run(_send_notification_async(id_rendez_vous, event))
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
            asyncio.run(_handle_webhook_async(passerelle, event))
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
            asyncio.run(_do_refund_async(id_rendez_vous, Decimal(str(montant))))
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
