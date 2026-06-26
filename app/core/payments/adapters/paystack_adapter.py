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
        montant: Decimal,
        devise: str,
        metadata: Optional[dict] = None,
    ) -> PaymentIntent:
        """
        Initialise une transaction Paystack.
        Retourne un PaymentIntent dont client_secret contient l'authorization_url.
        Le montant est en unités de base : kobo (NGN), pesewas (GHS), XAF directement.
        """
        meta = metadata or {}

        if not self._secret_key:
            reference = f"test_ref_{meta.get('id_rendez_vous', 'inconnu')}"
            return PaymentIntent(
                id=reference,
                montant=montant,
                devise=devise,
                statut="pending",
                client_secret="https://checkout.paystack.com/test",
            )

        async with httpx.AsyncClient() as client:
            reponse = await client.post(
                f"{self.BASE_URL}/transaction/initialize",
                json={
                    "montant": int(montant * 100),
                    "devise": devise.upper(),
                    "courriel": meta.get("patient_email", "patient@clinique.app"),
                    "metadata": meta,
                    "callback_url": meta.get("callback_url", ""),
                },
                headers=self._headers,
                timeout=30.0,
            )
            reponse.raise_for_status()
            donnees = reponse.json()["data"]
            return PaymentIntent(
                id=donnees["reference"],
                montant=montant,
                devise=devise.upper(),
                statut="pending",
                client_secret=donnees["authorization_url"],
            )

    async def confirm_payment(self, payment_intent_id: str) -> PaymentIntent:
        """Vérifie le statut d'une transaction Paystack par sa référence."""
        if not self._secret_key:
            return PaymentIntent(
                id=payment_intent_id,
                montant=Decimal("0"),
                devise="XAF",
                statut="succeeded",
                client_secret=None,
            )

        async with httpx.AsyncClient() as client:
            reponse = await client.get(
                f"{self.BASE_URL}/transaction/verify/{payment_intent_id}",
                headers=self._headers,
                timeout=30.0,
            )
            reponse.raise_for_status()
            donnees = reponse.json()["data"]
            statut = "succeeded" if donnees["statut"] == "success" else "failed"
            return PaymentIntent(
                id=str(donnees["id"]),
                montant=Decimal(str(donnees["montant"])) / 100,
                devise=donnees["devise"],
                statut=statut,
                client_secret=None,
            )

    async def refund(
        self, payment_intent_id: str, montant: Optional[Decimal] = None
    ) -> RefundResult:
        """Émet un remboursement partiel ou total via Paystack."""
        if not self._secret_key:
            return RefundResult(
                id=f"re_{payment_intent_id}",
                montant=montant or Decimal("0"),
                statut="refunded",
            )

        corps: dict = {"transaction": payment_intent_id}
        if montant is not None:
            corps["montant"] = int(montant * 100)

        async with httpx.AsyncClient() as client:
            reponse = await client.post(
                f"{self.BASE_URL}/refund",
                json=corps,
                headers=self._headers,
                timeout=30.0,
            )
            reponse.raise_for_status()
            donnees = reponse.json()["data"]
            montant_rembourse = Decimal(str(donnees.get("montant", 0))) / 100
            return RefundResult(
                id=str(donnees.get("id", "")),
                montant=montant_rembourse,
                statut="refunded",
            )

    async def get_payment(self, payment_intent_id: str) -> PaymentIntent:
        """Récupère l'état courant d'une transaction Paystack."""
        return await self.confirm_payment(payment_intent_id)

    async def verify_webhook(self, payload: bytes, signature: str) -> dict:
        """Vérifie la signature HMAC-SHA512 de Paystack."""
        if not self._secret_key:
            return json.loads(payload)

        signature_calculee = hmac.new(
            self._secret_key.encode(), payload, digestmod=hashlib.sha512
        ).hexdigest()
        if not hmac.compare_digest(signature_calculee, signature):
            raise ValueError("Signature de webhook Paystack invalide")
        return json.loads(payload)
