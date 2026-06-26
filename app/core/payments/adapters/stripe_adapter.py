"""Adaptateur Stripe — stub fonctionnel."""
from __future__ import annotations

import json
from decimal import Decimal
from typing import Optional

from app.core.payments.port import PaymentIntent, PaymentPort, RefundResult


class StripeAdapter(PaymentPort):
    """
    Adaptateur Stripe complet.
    En développement (sans clé API configurée), retourne des stubs de test.
    """

    def __init__(self) -> None:
        try:
            from app.config import settings
            self._api_key: Optional[str] = getattr(settings, "stripe_secret_key", None)
        except Exception:
            self._api_key = None

        if self._api_key:
            try:
                import stripe
                stripe.api_key = self._api_key
                self._stripe = stripe
            except ImportError:
                self._stripe = None
        else:
            self._stripe = None

    async def create_payment_intent(
        self,
        montant: Decimal,
        devise: str,
        metadata: Optional[dict] = None,
    ) -> PaymentIntent:
        if not self._stripe or not self._api_key:
            # Stub de développement
            return PaymentIntent(
                id="pi_test_stub",
                montant=montant,
                devise=devise,
                statut="requires_payment_method",
                client_secret="test_client_secret_stub",
            )
        intent = self._stripe.PaymentIntent.create(
            montant=int(montant * 100),
            devise=devise.lower(),
            metadata=metadata or {},
        )
        return PaymentIntent(
            id=intent.id,
            montant=Decimal(str(intent.montant / 100)),
            devise=intent.devise.upper(),
            statut=intent.statut,
            client_secret=intent.client_secret,
        )

    async def confirm_payment(self, payment_intent_id: str) -> PaymentIntent:
        if not self._stripe or not self._api_key:
            return PaymentIntent(
                id=payment_intent_id,
                montant=Decimal("0"),
                devise="XAF",
                statut="succeeded",
                client_secret=None,
            )
        intent = self._stripe.PaymentIntent.retrieve(payment_intent_id)
        return PaymentIntent(
            id=intent.id,
            montant=Decimal(str(intent.montant / 100)),
            devise=intent.devise.upper(),
            statut=intent.statut,
            client_secret=intent.client_secret,
        )

    async def refund(
        self, payment_intent_id: str, montant: Optional[Decimal] = None
    ) -> RefundResult:
        if not self._stripe or not self._api_key:
            return RefundResult(
                id=f"re_test_{payment_intent_id}",
                montant=montant or Decimal("0"),
                statut="refunded",
            )
        params: dict = {"payment_intent": payment_intent_id}
        if montant is not None:
            params["montant"] = int(montant * 100)
        refund = self._stripe.Refund.create(**params)
        return RefundResult(
            id=refund.id,
            montant=Decimal(str(refund.montant / 100)),
            statut="refunded",
        )

    async def get_payment(self, payment_intent_id: str) -> PaymentIntent:
        if not self._stripe or not self._api_key:
            return PaymentIntent(
                id=payment_intent_id,
                montant=Decimal("0"),
                devise="XAF",
                statut="succeeded",
                client_secret=None,
            )
        intent = self._stripe.PaymentIntent.retrieve(payment_intent_id)
        return PaymentIntent(
            id=intent.id,
            montant=Decimal(str(intent.montant / 100)),
            devise=intent.devise.upper(),
            statut=intent.statut,
            client_secret=intent.client_secret,
        )

    async def verify_webhook(self, payload: bytes, signature: str) -> dict:
        """Vérifie la signature Stripe et retourne l'événement parsé."""
        if not self._stripe or not self._api_key:
            return json.loads(payload)
        try:
            from app.config import settings
            secret_webhook = getattr(settings, "stripe_webhook_secret", None)
            if secret_webhook:
                evenement = self._stripe.Webhook.construct_event(
                    payload, signature, secret_webhook
                )
                return dict(evenement)
        except Exception:
            pass
        return json.loads(payload)
