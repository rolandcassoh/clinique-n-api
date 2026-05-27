"""Adaptateur Paystack — API v1."""
from __future__ import annotations

import hashlib
import hmac
import json
from decimal import Decimal
from typing import Optional

import httpx

from app.core.payments.port import PaymentIntent, PaymentPort, RefundResult


class PaystackAdapter(PaymentPort):
    """
    Adaptateur Paystack complet.
    Paystack utilise des 'transactions' plutôt que des payment intents.
    En développement (sans clé API configurée), retourne des stubs.
    """

    BASE_URL = "https://api.paystack.co"

    def __init__(self) -> None:
        try:
            from app.config import settings
            self._secret_key: Optional[str] = getattr(settings, "paystack_secret_key", None) or None
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
        Initialise une transaction Paystack.
        Retourne un PaymentIntent dont client_secret contient l'authorization_url.
        amount en unités de base : kobo (NGN), pesewas (GHS), XAF directement.
        """
        meta = metadata or {}

        if not self._secret_key:
            ref = f"test_ref_{meta.get('appointment_id', 'unknown')}"
            return PaymentIntent(
                id=ref,
                amount=amount,
                currency=currency,
                status="pending",
                client_secret="https://checkout.paystack.com/test",
            )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/transaction/initialize",
                json={
                    "amount": int(amount * 100),
                    "currency": currency.upper(),
                    "email": meta.get("patient_email", "patient@clinique.app"),
                    "metadata": meta,
                    "callback_url": meta.get("callback_url", ""),
                },
                headers=self._headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()["data"]
            return PaymentIntent(
                id=data["reference"],
                amount=amount,
                currency=currency.upper(),
                status="pending",
                client_secret=data["authorization_url"],
            )

    async def confirm_payment(self, payment_intent_id: str) -> PaymentIntent:
        """Vérifie le statut d'une transaction Paystack par sa référence."""
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
                f"{self.BASE_URL}/transaction/verify/{payment_intent_id}",
                headers=self._headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()["data"]
            status = "succeeded" if data["status"] == "success" else "failed"
            return PaymentIntent(
                id=str(data["id"]),
                amount=Decimal(str(data["amount"])) / 100,
                currency=data["currency"],
                status=status,
                client_secret=None,
            )

    async def refund(
        self, payment_intent_id: str, amount: Optional[Decimal] = None
    ) -> RefundResult:
        """Émet un remboursement partiel ou total via Paystack."""
        if not self._secret_key:
            return RefundResult(
                id=f"re_{payment_intent_id}",
                amount=amount or Decimal("0"),
                status="refunded",
            )

        payload: dict = {"transaction": payment_intent_id}
        if amount is not None:
            payload["amount"] = int(amount * 100)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/refund",
                json=payload,
                headers=self._headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()["data"]
            refunded_amount = Decimal(str(data.get("amount", 0))) / 100
            return RefundResult(
                id=str(data.get("id", "")),
                amount=refunded_amount,
                status="refunded",
            )

    async def get_payment(self, payment_intent_id: str) -> PaymentIntent:
        """Récupère l'état courant d'une transaction Paystack."""
        return await self.confirm_payment(payment_intent_id)

    async def verify_webhook(self, payload: bytes, signature: str) -> dict:
        """Vérifie la signature HMAC-SHA512 de Paystack."""
        if not self._secret_key:
            return json.loads(payload)

        computed = hmac.new(
            self._secret_key.encode(), payload, digestmod=hashlib.sha512
        ).hexdigest()
        if not hmac.compare_digest(computed, signature):
            raise ValueError("Invalid Paystack webhook signature")
        return json.loads(payload)
