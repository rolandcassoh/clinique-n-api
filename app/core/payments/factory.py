"""Factory pour les adaptateurs de paiement."""
from __future__ import annotations

from app.core.payments.port import PaymentPort

_SUPPORTED_GATEWAYS = ("stripe", "razorpay", "paypal", "paystack", "flutterwave", "wallet")


def get_payment_adapter(passerelle: str) -> PaymentPort:
    """
    Retourne l'adaptateur paiement correspondant à la passerelle.

    Args:
        passerelle: 'stripe' | 'razorpay' | 'paypal' | 'paystack' | 'flutterwave' | 'wallet'

    Raises:
        ValueError: Si la passerelle est inconnue.
    """
    if passerelle == "stripe":
        from app.core.payments.adapters.stripe_adapter import StripeAdapter
        return StripeAdapter()
    elif passerelle == "razorpay":
        from app.core.payments.adapters.razorpay_adapter import RazorpayAdapter
        return RazorpayAdapter()
    elif passerelle == "paypal":
        from app.core.payments.adapters.paypal_adapter import PayPalAdapter
        return PayPalAdapter()
    elif passerelle == "paystack":
        from app.core.payments.adapters.paystack_adapter import PaystackAdapter
        return PaystackAdapter()
    elif passerelle == "flutterwave":
        from app.core.payments.adapters.flutterwave_adapter import FlutterwaveAdapter
        return FlutterwaveAdapter()
    elif passerelle == "wallet":
        # Le portefeuille interne est géré directement dans les use cases, sans adaptateur externe
        from app.core.payments.adapters.stripe_adapter import StripeAdapter
        return StripeAdapter()  # Repli — le wallet est traité en amont
    else:
        raise ValueError(
            f"Passerelle de paiement inconnue : '{passerelle}'. "
            f"Valeurs acceptées : {', '.join(_SUPPORTED_GATEWAYS)}"
        )
