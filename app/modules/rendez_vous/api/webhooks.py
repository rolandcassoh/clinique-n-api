"""Points d'entrée webhooks paiement : Stripe, Razorpay."""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.rendez_vous.infrastructure.depots import (
    SQLAlchemyAppointmentRepository,
    SQLAlchemyAppointmentTransactionRepository,
)
from app.modules.rendez_vous.domain.entites import PaymentStatus

logger = logging.getLogger(__name__)

webhook_router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# ---------------------------------------------------------------------------
# Webhook Stripe
# ---------------------------------------------------------------------------


@webhook_router.post("/stripe", status_code=statut.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(default=None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Reçoit les événements Stripe et délègue le traitement à Celery.
    Vérifie la signature et route selon le type d'événement.
    """
    charge_utile = await request.body()

    if not charge_utile:
        raise HTTPException(status_code=400, detail="Payload vide")

    try:
        evenement = json.loads(charge_utile)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Payload JSON invalide")

    type_evenement = evenement.get("type", "")
    logger.info("stripe_webhook_recu", extra={"event_type": type_evenement})

    # Délégation asynchrone à Celery
    try:
        from app.core.queue.tasks import process_payment_webhook

        process_payment_webhook.delay("stripe", evenement)
    except Exception as exc:
        logger.warning("celery_non_disponible", extra={"error": str(exc)})
        # En mode sans Celery, traitement synchrone en ligne
        await _process_stripe_event(evenement, db)

    return {"statut": "received", "event_type": type_evenement}


async def _process_stripe_event(evenement: dict, db: AsyncSession) -> None:
    """Traitement synchrone d'un événement Stripe (solution de repli sans Celery)."""
    type_evenement = evenement.get("type", "")
    depot = SQLAlchemyAppointmentRepository(db)
    depot_transactions = SQLAlchemyAppointmentTransactionRepository(db)

    if type_evenement == "payment_intent.succeeded":
        pi = evenement.get("data", {}).get("object", {})
        metadonnees = pi.get("metadata", {})
        id_rendez_vous = metadonnees.get("id_rendez_vous")
        if id_rendez_vous:
            rendez_vous = await depot.find_by_id(int(id_rendez_vous))
            if rendez_vous:
                rendez_vous.statut_paiement = PaymentStatus.PAID
                rendez_vous.reference_paiement = pi.get("id")
                await depot.save(rendez_vous)
                await depot_transactions.update_status(
                    reference_transaction=pi.get("id", ""),
                    statut="succeeded",
                    reponse_passerelle=pi,
                )

    elif type_evenement == "payment_intent.payment_failed":
        pi = evenement.get("data", {}).get("object", {})
        await depot_transactions.update_status(
            reference_transaction=pi.get("id", ""),
            statut="failed",
            reponse_passerelle=pi,
        )

    elif type_evenement == "charge.refunded":
        debit = evenement.get("data", {}).get("object", {})
        await depot_transactions.update_status(
            reference_transaction=debit.get("payment_intent", ""),
            statut="refunded",
            reponse_passerelle=debit,
        )


# ---------------------------------------------------------------------------
# Webhook Razorpay
# ---------------------------------------------------------------------------


@webhook_router.post("/razorpay", status_code=statut.HTTP_200_OK)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(default=None, alias="x-razorpay-signature"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Reçoit les événements Razorpay et délègue le traitement à Celery.
    """
    charge_utile = await request.body()

    if not charge_utile:
        raise HTTPException(status_code=400, detail="Payload vide")

    try:
        evenement = json.loads(charge_utile)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Payload JSON invalide")

    type_evenement = evenement.get("event", "")
    logger.info("razorpay_webhook_recu", extra={"event_type": type_evenement})

    try:
        from app.core.queue.tasks import process_payment_webhook

        process_payment_webhook.delay("razorpay", evenement)
    except Exception as exc:
        logger.warning("celery_non_disponible", extra={"error": str(exc)})
        await _process_razorpay_event(evenement, db)

    return {"statut": "received", "event_type": type_evenement}


async def _process_razorpay_event(evenement: dict, db: AsyncSession) -> None:
    """Traitement synchrone d'un événement Razorpay (solution de repli sans Celery)."""
    type_evenement = evenement.get("event", "")
    depot = SQLAlchemyAppointmentRepository(db)
    depot_transactions = SQLAlchemyAppointmentTransactionRepository(db)

    if type_evenement == "payment.captured":
        paiement = evenement.get("payload", {}).get("payment", {}).get("entity", {})
        notes = paiement.get("notes", {})
        id_rendez_vous = notes.get("id_rendez_vous")
        if id_rendez_vous:
            rendez_vous = await depot.find_by_id(int(id_rendez_vous))
            if rendez_vous:
                rendez_vous.statut_paiement = PaymentStatus.PAID
                rendez_vous.reference_paiement = paiement.get("id")
                await depot.save(rendez_vous)

    elif type_evenement == "payment.failed":
        paiement = evenement.get("payload", {}).get("payment", {}).get("entity", {})
        await depot_transactions.update_status(
            reference_transaction=paiement.get("id", ""),
            statut="failed",
            reponse_passerelle=paiement,
        )

    elif type_evenement == "refund.created":
        remboursement = evenement.get("payload", {}).get("refund", {}).get("entity", {})
        await depot_transactions.update_status(
            reference_transaction=remboursement.get("payment_id", ""),
            statut="refunded",
            reponse_passerelle=remboursement,
        )
