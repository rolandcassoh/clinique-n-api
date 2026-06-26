"""Adaptateur Razorpay — stub fonctionnel."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.core.payments.port import PaymentIntent, PaymentPort, RefundResult


class RazorpayAdapter(PaymentPort):
    """
    Adaptateur Razorpay.
    En développement (sans clé API configurée), retourne des stubs.
    """

    def __init__(self) -> None:
        try:
            from app.config import settings
            self._key_id: Optional[str] = getattr(settings, "razorpay_key_id", None)
            self._key_secret: Optional[str] = getattr(settings, "razorpay_key_secret", None)
        except Exception:
            self._key_id = None
            self._key_secret = None

        self._client = None
        if self._key_id and self._key_secret:
            try:
                import razorpay  # type: ignore
                self._client = razorpay.Client(
                    auth=(self._key_id, self._key_secret)
                )
            except ImportError:
                self._client = None

    async def create_payment_intent(
        self,
        montant: Decimal,
        devise: str,
        metadata: Optional[dict] = None,
    ) -> PaymentIntent:
        if not self._client:
            return PaymentIntent(
                id="order_test_stub",
                montant=montant,
                devise=devise,
                statut="created",
                client_secret=None,
            )
        order = self._client.order.create(
            {
                "montant": int(montant * 100),
                "devise": devise.upper(),
                "notes": metadata or {},
            }
        )
        return PaymentIntent(
            id=order["id"],
            montant=Decimal(str(order["montant"] / 100)),
            devise=order["devise"],
            statut=order["statut"],
            client_secret=None,
        )

    async def confirm_payment(self, payment_intent_id: str) -> PaymentIntent:
        if not self._client:
            return PaymentIntent(
                id=payment_intent_id,
                montant=Decimal("0"),
                devise="INR",
                statut="captured",
                client_secret=None,
            )
        payment = self._client.payment.fetch(payment_intent_id)
        return PaymentIntent(
            id=payment["id"],
            montant=Decimal(str(payment["montant"] / 100)),
            devise=payment["devise"],
            statut=payment["statut"],
            client_secret=None,
        )

    async def refund(
        self, payment_intent_id: str, montant: Optional[Decimal] = None
    ) -> RefundResult:
        if not self._client:
            return RefundResult(
                id=f"rfnd_test_{payment_intent_id}",
                montant=montant or Decimal("0"),
                statut="refunded",
            )
        params: dict = {}
        if montant is not None:
            params["montant"] = int(montant * 100)
        refund = self._client.payment.refund(payment_intent_id, params)
        return RefundResult(
            id=refund["id"],
            montant=Decimal(str(refund["montant"] / 100)),
            statut="refunded",
        )

    async def get_payment(self, payment_intent_id: str) -> PaymentIntent:
        if not self._client:
            return PaymentIntent(
                id=payment_intent_id,
                montant=Decimal("0"),
                devise="INR",
                statut="captured",
                client_secret=None,
            )
        payment = self._client.payment.fetch(payment_intent_id)
        return PaymentIntent(
            id=payment["id"],
            montant=Decimal(str(payment["montant"] / 100)),
            devise=payment["devise"],
            statut=payment["statut"],
            client_secret=None,
        )
