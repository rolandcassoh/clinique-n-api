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
        amount: Decimal,
        currency: str,
        metadata: Optional[dict] = None,
    ) -> PaymentIntent:
        if not self._client:
            return PaymentIntent(
                id="order_test_stub",
                amount=amount,
                currency=currency,
                status="created",
                client_secret=None,
            )
        order = self._client.order.create(
            {
                "amount": int(amount * 100),
                "currency": currency.upper(),
                "notes": metadata or {},
            }
        )
        return PaymentIntent(
            id=order["id"],
            amount=Decimal(str(order["amount"] / 100)),
            currency=order["currency"],
            status=order["status"],
            client_secret=None,
        )

    async def confirm_payment(self, payment_intent_id: str) -> PaymentIntent:
        if not self._client:
            return PaymentIntent(
                id=payment_intent_id,
                amount=Decimal("0"),
                currency="INR",
                status="captured",
                client_secret=None,
            )
        payment = self._client.payment.fetch(payment_intent_id)
        return PaymentIntent(
            id=payment["id"],
            amount=Decimal(str(payment["amount"] / 100)),
            currency=payment["currency"],
            status=payment["status"],
            client_secret=None,
        )

    async def refund(
        self, payment_intent_id: str, amount: Optional[Decimal] = None
    ) -> RefundResult:
        if not self._client:
            return RefundResult(
                id=f"rfnd_test_{payment_intent_id}",
                amount=amount or Decimal("0"),
                status="refunded",
            )
        params: dict = {}
        if amount is not None:
            params["amount"] = int(amount * 100)
        refund = self._client.payment.refund(payment_intent_id, params)
        return RefundResult(
            id=refund["id"],
            amount=Decimal(str(refund["amount"] / 100)),
            status="refunded",
        )

    async def get_payment(self, payment_intent_id: str) -> PaymentIntent:
        if not self._client:
            return PaymentIntent(
                id=payment_intent_id,
                amount=Decimal("0"),
                currency="INR",
                status="captured",
                client_secret=None,
            )
        payment = self._client.payment.fetch(payment_intent_id)
        return PaymentIntent(
            id=payment["id"],
            amount=Decimal(str(payment["amount"] / 100)),
            currency=payment["currency"],
            status=payment["status"],
            client_secret=None,
        )
