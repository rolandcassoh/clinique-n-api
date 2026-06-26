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
        montant: Decimal,
        devise: str,
        metadata: Optional[dict] = None,
    ) -> PaymentIntent:
        """
        Crée un lien de paiement Flutterwave (hosted payment page).
        Retourne un PaymentIntent dont client_secret contient le payment_link.
        """
        meta = metadata or {}

        if not self._secret_key:
            tx_ref = f"FLW-{meta.get('id_rendez_vous', 'unknown')}"
            return PaymentIntent(
                id=tx_ref,
                montant=montant,
                devise=devise,
                statut="pending",
                client_secret="https://checkout.flutterwave.com/test",
            )

        tx_ref = f"FLW-{uuid.uuid4().hex[:12].upper()}"

        async with httpx.AsyncClient() as client:
            reponse = await client.post(
                f"{self.BASE_URL}/payments",
                json={
                    "tx_ref": tx_ref,
                    "montant": float(montant),
                    "devise": devise.upper(),
                    "redirect_url": meta.get("callback_url", ""),
                    "customer": {
                        "courriel": meta.get("patient_email", "patient@clinique.app"),
                        "nom": meta.get("patient_name", "Patient"),
                    },
                    "meta": meta,
                },
                headers=self._headers,
                timeout=30.0,
            )
            reponse.raise_for_status()
            donnees = reponse.json()["data"]
            return PaymentIntent(
                id=tx_ref,
                montant=montant,
                devise=devise.upper(),
                statut="pending",
                client_secret=donnees["lien"],
            )

    async def confirm_payment(self, payment_intent_id: str) -> PaymentIntent:
        """Vérifie le statut d'une transaction Flutterwave par son ID."""
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
                f"{self.BASE_URL}/transactions/{payment_intent_id}/verify",
                headers=self._headers,
                timeout=30.0,
            )
            reponse.raise_for_status()
            donnees = reponse.json()["data"]
            statut = "succeeded" if donnees["statut"] == "successful" else "failed"
            return PaymentIntent(
                id=str(donnees["id"]),
                montant=Decimal(str(donnees["montant"])),
                devise=donnees["devise"],
                statut=statut,
                client_secret=None,
            )

    async def refund(
        self, payment_intent_id: str, montant: Optional[Decimal] = None
    ) -> RefundResult:
        """Émet un remboursement via Flutterwave."""
        if not self._secret_key:
            return RefundResult(
                id=f"ref_{payment_intent_id}",
                montant=montant or Decimal("0"),
                statut="refunded",
            )

        corps: dict = {}
        if montant is not None:
            corps["montant"] = float(montant)

        async with httpx.AsyncClient() as client:
            reponse = await client.post(
                f"{self.BASE_URL}/transactions/{payment_intent_id}/refund",
                json=corps,
                headers=self._headers,
                timeout=30.0,
            )
            reponse.raise_for_status()
            donnees = reponse.json()["data"]
            montant_rembourse = Decimal(str(donnees.get("amount_refunded", montant or 0)))
            return RefundResult(
                id=str(donnees.get("id", "")),
                montant=montant_rembourse,
                statut="refunded",
            )

    async def get_payment(self, payment_intent_id: str) -> PaymentIntent:
        """Récupère l'état courant d'une transaction Flutterwave."""
        return await self.confirm_payment(payment_intent_id)

    async def verify_webhook(self, payload: bytes, signature: str) -> dict:
        """
        Flutterwave utilise un hash secret statique en en-tête (verif-hash).
        Compare la signature avec la flutterwave_secret_key.
        """
        if not self._secret_key:
            return json.loads(payload)

        if signature != self._secret_key:
            raise ValueError("Signature de webhook Flutterwave invalide")
        return json.loads(payload)
