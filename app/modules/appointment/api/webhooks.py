"""Endpoints webhooks paiement : Stripe, Razorpay."""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.appointment.infrastructure.repositories import (
    SQLAlchemyAppointmentRepository,
    SQLAlchemyAppointmentTransactionRepository,
)
from app.modules.appointment.domain.entities import PaymentStatus

logger = logging.getLogger(__name__)

webhook_router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# ---------------------------------------------------------------------------
# Stripe webhook
# ---------------------------------------------------------------------------


@webhook_router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(default=None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Reçoit les événements Stripe et délègue le traitement à Celery.
    Vérifie la signature et route selon l'event type.
    """
    payload = await request.body()

    if not payload:
        raise HTTPException(status_code=400, detail="Payload vide")

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Payload JSON invalide")

    event_type = event.get("type", "")
    logger.info("stripe_webhook_received", extra={"event_type": event_type})

    # Délégation async à Celery
    try:
        from app.core.queue.tasks import process_payment_webhook

        process_payment_webhook.delay("stripe", event)
    except Exception as exc:
        logger.warning("celery_not_available", extra={"error": str(exc)})
        # En mode sans Celery, traitement inline
        await _process_stripe_event(event, db)

    return {"status": "received", "event_type": event_type}


async def _process_stripe_event(event: dict, db: AsyncSession) -> None:
    """Traitement inline d'un événement Stripe (fallback sans Celery)."""
    event_type = event.get("type", "")
    repo = SQLAlchemyAppointmentRepository(db)
    tx_repo = SQLAlchemyAppointmentTransactionRepository(db)

    if event_type == "payment_intent.succeeded":
        pi = event.get("data", {}).get("object", {})
        metadata = pi.get("metadata", {})
        appointment_id = metadata.get("appointment_id")
        if appointment_id:
            appointment = await repo.find_by_id(int(appointment_id))
            if appointment:
                appointment.payment_status = PaymentStatus.PAID
                appointment.payment_reference = pi.get("id")
                await repo.save(appointment)
                await tx_repo.update_status(
                    transaction_ref=pi.get("id", ""),
                    status="succeeded",
                    gateway_response=pi,
                )

    elif event_type == "payment_intent.payment_failed":
        pi = event.get("data", {}).get("object", {})
        await tx_repo.update_status(
            transaction_ref=pi.get("id", ""),
            status="failed",
            gateway_response=pi,
        )

    elif event_type == "charge.refunded":
        charge = event.get("data", {}).get("object", {})
        await tx_repo.update_status(
            transaction_ref=charge.get("payment_intent", ""),
            status="refunded",
            gateway_response=charge,
        )


# ---------------------------------------------------------------------------
# Razorpay webhook
# ---------------------------------------------------------------------------


@webhook_router.post("/razorpay", status_code=status.HTTP_200_OK)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(default=None, alias="x-razorpay-signature"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Reçoit les événements Razorpay et délègue le traitement à Celery.
    """
    payload = await request.body()

    if not payload:
        raise HTTPException(status_code=400, detail="Payload vide")

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Payload JSON invalide")

    event_type = event.get("event", "")
    logger.info("razorpay_webhook_received", extra={"event_type": event_type})

    try:
        from app.core.queue.tasks import process_payment_webhook

        process_payment_webhook.delay("razorpay", event)
    except Exception as exc:
        logger.warning("celery_not_available", extra={"error": str(exc)})
        await _process_razorpay_event(event, db)

    return {"status": "received", "event_type": event_type}


async def _process_razorpay_event(event: dict, db: AsyncSession) -> None:
    """Traitement inline d'un événement Razorpay (fallback sans Celery)."""
    event_type = event.get("event", "")
    repo = SQLAlchemyAppointmentRepository(db)
    tx_repo = SQLAlchemyAppointmentTransactionRepository(db)

    if event_type == "payment.captured":
        payment = event.get("payload", {}).get("payment", {}).get("entity", {})
        notes = payment.get("notes", {})
        appointment_id = notes.get("appointment_id")
        if appointment_id:
            appointment = await repo.find_by_id(int(appointment_id))
            if appointment:
                appointment.payment_status = PaymentStatus.PAID
                appointment.payment_reference = payment.get("id")
                await repo.save(appointment)

    elif event_type == "payment.failed":
        payment = event.get("payload", {}).get("payment", {}).get("entity", {})
        await tx_repo.update_status(
            transaction_ref=payment.get("id", ""),
            status="failed",
            gateway_response=payment,
        )

    elif event_type == "refund.created":
        refund = event.get("payload", {}).get("refund", {}).get("entity", {})
        await tx_repo.update_status(
            transaction_ref=refund.get("payment_id", ""),
            status="refunded",
            gateway_response=refund,
        )
