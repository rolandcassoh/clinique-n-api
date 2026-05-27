"""Adaptateur Flutterwave — API v3."""
from __future__ import annotations

import json
import uuid
from decimal import Decimal
from typing import Optional

import httpx

from app.core.payments.port import PaymentIntent, PaymentPort, RefundResult


class FlutterwaveAdapter(PaymentPort):
    """
    Adaptateur Flutterwave complet.
    Flutterwave utilise des hosted payment pages via /payments.
    En développement (sans clé API configurée), retourne des stubs.
    """

    BASE_URL = "https://api.flutterwave.com/v3"

    def __init__(self) -> None:
        try:
            from app.config import settings
            self._secret_key: Optional[str] = getattr(settings, "flutterwave_secret_key", None) or None
        except Exception:
            self._secret_key = None

        self._headers = {
            "Authorization": f"Bearer {self._secret_key or ''}",
            "Content-Type": "application/json",
        }

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        metadata: Optional[dict] = None,
    ) -> PaymentIntent:
        """
        Crée un lien de paiement Flutterwave (hosted payment page).
        Retourne un PaymentIntent dont client_secret contient le payment_link.
        """
        meta = metadata or {}

        if not self._secret_key:
            tx_ref = f"FLW-{meta.get('appointment_id', 'unknown')}"
            return PaymentIntent(
                id=tx_ref,
                amount=amount,
                currency=currency,
                status="pending",
                client_secret="https://checkout.flutterwave.com/test",
            )

        tx_ref = f"FLW-{uuid.uuid4().hex[:12].upper()}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/payments",
                json={
                    "tx_ref": tx_ref,
                    "amount": float(amount),
                    "currency": currency.upper(),
                    "redirect_url": meta.get("callback_url", ""),
                    "customer": {
                        "email": meta.get("patient_email", "patient@clinique.app"),
                        "name": meta.get("patient_name", "Patient"),
                    },
                    "meta": meta,
                },
                headers=self._headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()["data"]
            return PaymentIntent(
                id=tx_ref,
                amount=amount,
                currency=currency.upper(),
                status="pending",
                client_secret=data["link"],
            )

    async def confirm_payment(self, payment_intent_id: str) -> PaymentIntent:
        """Vérifie le statut d'une transaction Flutterwave par son ID."""
        if not self._secret_key:
            return PaymentIntent(
                id=payment_intent_id,
                amount=Decimal("0"),
                currency="XAF",
                status="succeeded",
                client_secret=None,
            )

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/transactions/{payment_intent_id}/verify",
                headers=self._headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()["data"]
            status = "succeeded" if data["status"] == "successful" else "failed"
            return PaymentIntent(
                id=str(data["id"]),
                amount=Decimal(str(data["amount"])),
                currency=data["currency"],
                status=status,
                client_secret=None,
            )

    async def refund(
        self, payment_intent_id: str, amount: Optional[Decimal] = None
    ) -> RefundResult:
        """Émet un remboursement via Flutterwave."""
        if not self._secret_key:
            return RefundResult(
                id=f"ref_{payment_intent_id}",
                amount=amount or Decimal("0"),
                status="refunded",
            )

        payload: dict = {}
        if amount is not None:
            payload["amount"] = float(amount)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/transactions/{payment_intent_id}/refund",
                json=payload,
                headers=self._headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()["data"]
            refunded_amount = Decimal(str(data.get("amount_refunded", amount or 0)))
            return RefundResult(
                id=str(data.get("id", "")),
                amount=refunded_amount,
                status="refunded",
            )

    async def get_payment(self, payment_intent_id: str) -> PaymentIntent:
        """Récupère l'état courant d'une transaction Flutterwave."""
        return await self.confirm_payment(payment_intent_id)

    async def verify_webhook(self, payload: bytes, signature: str) -> dict:
        """
        Flutterwave utilise un secret hash statique en header (verif-hash).
        Compare la signature avec la flutterwave_secret_key.
        """
        if not self._secret_key:
            return json.loads(payload)

        if signature != self._secret_key:
            raise ValueError("Invalid Flutterwave webhook signature")
        return json.loads(payload)
