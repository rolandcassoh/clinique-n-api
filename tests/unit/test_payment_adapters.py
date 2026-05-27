"""Tests unitaires des adaptateurs de paiement (mode stub sans clés API)."""
from __future__ import annotations

import json
import hashlib
import hmac
from decimal import Decimal

import pytest

from app.core.payments.port import PaymentIntent, RefundResult


# ---------------------------------------------------------------------------
# Factory — routing et cas d'erreur
# ---------------------------------------------------------------------------

class TestPaymentFactory:
    def test_get_stripe_adapter(self):
        from app.core.payments.factory import get_payment_adapter
        from app.core.payments.adapters.stripe_adapter import StripeAdapter

        adapter = get_payment_adapter("stripe")
        assert isinstance(adapter, StripeAdapter)

    def test_get_razorpay_adapter(self):
        from app.core.payments.factory import get_payment_adapter
        from app.core.payments.adapters.razorpay_adapter import RazorpayAdapter

        adapter = get_payment_adapter("razorpay")
        assert isinstance(adapter, RazorpayAdapter)

    def test_get_paypal_adapter(self):
        from app.core.payments.factory import get_payment_adapter
        from app.core.payments.adapters.paypal_adapter import PayPalAdapter

        adapter = get_payment_adapter("paypal")
        assert isinstance(adapter, PayPalAdapter)

    def test_get_paystack_adapter(self):
        from app.core.payments.factory import get_payment_adapter
        from app.core.payments.adapters.paystack_adapter import PaystackAdapter

        adapter = get_payment_adapter("paystack")
        assert isinstance(adapter, PaystackAdapter)

    def test_get_flutterwave_adapter(self):
        from app.core.payments.factory import get_payment_adapter
        from app.core.payments.adapters.flutterwave_adapter import FlutterwaveAdapter

        adapter = get_payment_adapter("flutterwave")
        assert isinstance(adapter, FlutterwaveAdapter)

    def test_unknown_gateway_raises_value_error(self):
        from app.core.payments.factory import get_payment_adapter

        with pytest.raises(ValueError, match="inconnue"):
            get_payment_adapter("unknown_gateway")

    def test_unknown_gateway_error_message_contains_name(self):
        from app.core.payments.factory import get_payment_adapter

        with pytest.raises(ValueError) as exc_info:
            get_payment_adapter("bitcoin")
        assert "bitcoin" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Adaptateur Stripe — mode stub
# ---------------------------------------------------------------------------

class TestStripeAdapterStub:
    @pytest.fixture
    def adapter(self):
        from app.core.payments.adapters.stripe_adapter import StripeAdapter
        a = StripeAdapter()
        a._api_key = None
        a._stripe = None
        return a

    @pytest.mark.asyncio
    async def test_create_payment_intent_returns_stub(self, adapter):
        result = await adapter.create_payment_intent(
            Decimal("5000"), "XAF", {"appointment_id": "123"}
        )
        assert isinstance(result, PaymentIntent)
        assert result.id == "pi_test_stub"
        assert result.amount == Decimal("5000")
        assert result.currency == "XAF"

    @pytest.mark.asyncio
    async def test_confirm_payment_returns_stub(self, adapter):
        result = await adapter.confirm_payment("pi_test_stub")
        assert isinstance(result, PaymentIntent)
        assert result.status == "succeeded"

    @pytest.mark.asyncio
    async def test_refund_returns_stub(self, adapter):
        result = await adapter.refund("pi_test_stub", Decimal("1000"))
        assert isinstance(result, RefundResult)
        assert result.status == "refunded"
        assert result.amount == Decimal("1000")

    @pytest.mark.asyncio
    async def test_get_payment_returns_stub(self, adapter):
        result = await adapter.get_payment("pi_test_stub")
        assert isinstance(result, PaymentIntent)
        assert result.status == "succeeded"


# ---------------------------------------------------------------------------
# Adaptateur Paystack — mode stub
# ---------------------------------------------------------------------------

class TestPaystackAdapterStub:
    @pytest.fixture
    def adapter(self):
        from app.core.payments.adapters.paystack_adapter import PaystackAdapter
        a = PaystackAdapter()
        a._secret_key = None
        a._headers = {}
        return a

    @pytest.mark.asyncio
    async def test_create_payment_intent_returns_stub(self, adapter):
        result = await adapter.create_payment_intent(
            Decimal("10000"), "NGN", {"appointment_id": "abc"}
        )
        assert isinstance(result, PaymentIntent)
        assert "test_ref_abc" in result.id
        assert result.status == "pending"
        assert result.client_secret == "https://checkout.paystack.com/test"

    @pytest.mark.asyncio
    async def test_confirm_payment_returns_stub(self, adapter):
        result = await adapter.confirm_payment("test_ref_abc")
        assert isinstance(result, PaymentIntent)
        assert result.status == "succeeded"
        assert result.currency == "XAF"

    @pytest.mark.asyncio
    async def test_refund_returns_stub(self, adapter):
        result = await adapter.refund("12345", Decimal("2000"))
        assert isinstance(result, RefundResult)
        assert result.status == "refunded"
        assert result.amount == Decimal("2000")
        assert "12345" in result.id

    @pytest.mark.asyncio
    async def test_get_payment_delegates_to_confirm(self, adapter):
        result = await adapter.get_payment("some_ref")
        assert isinstance(result, PaymentIntent)
        assert result.status == "succeeded"

    @pytest.mark.asyncio
    async def test_verify_webhook_no_key_returns_parsed_json(self, adapter):
        payload = json.dumps({"event": "charge.success"}).encode()
        result = await adapter.verify_webhook(payload, "any_sig")
        assert result["event"] == "charge.success"

    @pytest.mark.asyncio
    async def test_verify_webhook_invalid_signature_raises(self):
        from app.core.payments.adapters.paystack_adapter import PaystackAdapter
        a = PaystackAdapter()
        a._secret_key = "real_secret_key"

        payload = json.dumps({"event": "charge.success"}).encode()
        with pytest.raises(ValueError, match="Invalid Paystack webhook signature"):
            await a.verify_webhook(payload, "bad_signature")

    @pytest.mark.asyncio
    async def test_verify_webhook_valid_signature_succeeds(self):
        from app.core.payments.adapters.paystack_adapter import PaystackAdapter
        a = PaystackAdapter()
        a._secret_key = "real_secret_key"
        a._headers = {}

        payload = json.dumps({"event": "charge.success"}).encode()
        valid_sig = hmac.new(
            b"real_secret_key", payload, digestmod=hashlib.sha512
        ).hexdigest()
        result = await a.verify_webhook(payload, valid_sig)
        assert result["event"] == "charge.success"


# ---------------------------------------------------------------------------
# Adaptateur Flutterwave — mode stub
# ---------------------------------------------------------------------------

class TestFlutterwaveAdapterStub:
    @pytest.fixture
    def adapter(self):
        from app.core.payments.adapters.flutterwave_adapter import FlutterwaveAdapter
        a = FlutterwaveAdapter()
        a._secret_key = None
        a._headers = {}
        return a

    @pytest.mark.asyncio
    async def test_create_payment_intent_returns_stub(self, adapter):
        result = await adapter.create_payment_intent(
            Decimal("15000"), "XAF", {"appointment_id": "xyz"}
        )
        assert isinstance(result, PaymentIntent)
        assert "xyz" in result.id
        assert result.status == "pending"
        assert result.client_secret == "https://checkout.flutterwave.com/test"

    @pytest.mark.asyncio
    async def test_confirm_payment_returns_stub(self, adapter):
        result = await adapter.confirm_payment("flw_tx_123")
        assert isinstance(result, PaymentIntent)
        assert result.status == "succeeded"

    @pytest.mark.asyncio
    async def test_refund_returns_stub(self, adapter):
        result = await adapter.refund("flw_tx_123", Decimal("5000"))
        assert isinstance(result, RefundResult)
        assert result.status == "refunded"
        assert result.amount == Decimal("5000")
        assert "flw_tx_123" in result.id

    @pytest.mark.asyncio
    async def test_get_payment_delegates_to_confirm(self, adapter):
        result = await adapter.get_payment("flw_tx_456")
        assert isinstance(result, PaymentIntent)
        assert result.status == "succeeded"

    @pytest.mark.asyncio
    async def test_verify_webhook_no_key_returns_parsed_json(self, adapter):
        payload = json.dumps({"event": "charge.completed"}).encode()
        result = await adapter.verify_webhook(payload, "any_sig")
        assert result["event"] == "charge.completed"

    @pytest.mark.asyncio
    async def test_verify_webhook_invalid_signature_raises(self):
        from app.core.payments.adapters.flutterwave_adapter import FlutterwaveAdapter
        a = FlutterwaveAdapter()
        a._secret_key = "my_flw_secret"

        payload = json.dumps({"event": "charge.completed"}).encode()
        with pytest.raises(ValueError, match="Invalid Flutterwave webhook signature"):
            await a.verify_webhook(payload, "wrong_secret")

    @pytest.mark.asyncio
    async def test_verify_webhook_correct_secret_succeeds(self):
        from app.core.payments.adapters.flutterwave_adapter import FlutterwaveAdapter
        a = FlutterwaveAdapter()
        a._secret_key = "my_flw_secret"

        payload = json.dumps({"event": "charge.completed"}).encode()
        result = await a.verify_webhook(payload, "my_flw_secret")
        assert result["event"] == "charge.completed"
