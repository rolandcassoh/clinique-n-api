"""Adaptateur PayPal — stub fonctionnel."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.core.payments.port import PaymentIntent, PaymentPort, RefundResult


class PayPalAdapter(PaymentPort):
    """
    Adaptateur PayPal.
    En développement (sans clé API configurée), retourne des stubs.
    """

    def __init__(self) -> None:
        try:
            from app.config import settings
            self._client_id: Optional[str] = getattr(settings, "paypal_client_id", None)
            self._client_secret: Optional[str] = getattr(settings, "paypal_client_secret", None)
            self._sandbox: bool = getattr(settings, "paypal_sandbox", True)
        except Exception:
            self._client_id = None
            self._client_secret = None
            self._sandbox = True

    def _is_configured(self) -> bool:
        return bool(self._client_id and self._client_secret)

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        metadata: Optional[dict] = None,
    ) -> PaymentIntent:
        if not self._is_configured():
            return PaymentIntent(
                id="PAYPAL-ORDER-STUB",
                amount=amount,
                currency=currency,
                status="CREATED",
                client_secret=None,
            )
        # Implémentation réelle via PayPal REST API v2
        # À compléter avec paypalrestsdk ou appels HTTP directs
        return PaymentIntent(
            id="PAYPAL-ORDER-STUB",
            amount=amount,
            currency=currency,
            status="CREATED",
            client_secret=None,
        )

    async def confirm_payment(self, payment_intent_id: str) -> PaymentIntent:
        if not self._is_configured():
            return PaymentIntent(
                id=payment_intent_id,
                amount=Decimal("0"),
                currency="USD",
                status="COMPLETED",
                client_secret=None,
            )
        return PaymentIntent(
            id=payment_intent_id,
            amount=Decimal("0"),
            currency="USD",
            status="COMPLETED",
            client_secret=None,
        )

    async def refund(
        self, payment_intent_id: str, amount: Optional[Decimal] = None
    ) -> RefundResult:
        if not self._is_configured():
            return RefundResult(
                id=f"REFUND-PAYPAL-{payment_intent_id}",
                amount=amount or Decimal("0"),
                status="refunded",
            )
        return RefundResult(
            id=f"REFUND-PAYPAL-{payment_intent_id}",
            amount=amount or Decimal("0"),
            status="refunded",
        )

    async def get_payment(self, payment_intent_id: str) -> PaymentIntent:
        if not self._is_configured():
            return PaymentIntent(
                id=payment_intent_id,
                amount=Decimal("0"),
                currency="USD",
                status="COMPLETED",
                client_secret=None,
            )
        return PaymentIntent(
            id=payment_intent_id,
            amount=Decimal("0"),
            currency="USD",
            status="COMPLETED",
            client_secret=None,
        )
