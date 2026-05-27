"""Factory pour les adaptateurs de paiement."""
from __future__ import annotations

from app.core.payments.port import PaymentPort

_SUPPORTED_GATEWAYS = ("stripe", "razorpay", "paypal", "paystack", "flutterwave", "wallet")


def get_payment_adapter(gateway: str) -> PaymentPort:
    """
    Retourne l'adaptateur paiement correspondant à la passerelle.

    Args:
        gateway: 'stripe' | 'razorpay' | 'paypal' | 'paystack' | 'flutterwave' | 'wallet'

    Raises:
        ValueError: Si la passerelle est inconnue.
    """
    if gateway == "stripe":
        from app.core.payments.adapters.stripe_adapter import StripeAdapter
        return StripeAdapter()
    elif gateway == "razorpay":
        from app.core.payments.adapters.razorpay_adapter import RazorpayAdapter
        return RazorpayAdapter()
    elif gateway == "paypal":
        from app.core.payments.adapters.paypal_adapter import PayPalAdapter
        return PayPalAdapter()
    elif gateway == "paystack":
        from app.core.payments.adapters.paystack_adapter import PaystackAdapter
        return PaystackAdapter()
    elif gateway == "flutterwave":
        from app.core.payments.adapters.flutterwave_adapter import FlutterwaveAdapter
        return FlutterwaveAdapter()
    elif gateway == "wallet":
        # Wallet est géré directement dans les use cases sans adaptateur externe
        from app.core.payments.adapters.stripe_adapter import StripeAdapter
        return StripeAdapter()  # Fallback — wallet géré en amont
    else:
        raise ValueError(
            f"Passerelle de paiement inconnue : '{gateway}'. "
            f"Valeurs acceptées : {', '.join(_SUPPORTED_GATEWAYS)}"
        )
