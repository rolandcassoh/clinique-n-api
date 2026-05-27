from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PaymentIntent:
    id: str
    amount: Decimal
    currency: str
    status: str
    client_secret: str | None = None


@dataclass
class RefundResult:
    id: str
    amount: Decimal
    status: str


class PaymentPort(ABC):
    @abstractmethod
    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        metadata: dict[str, str] | None = None,
    ) -> PaymentIntent:
        """Create a payment intent and return it."""

    @abstractmethod
    async def confirm_payment(self, payment_intent_id: str) -> PaymentIntent:
        """Confirm an existing payment intent."""

    @abstractmethod
    async def refund(self, payment_intent_id: str, amount: Decimal | None = None) -> RefundResult:
        """Issue a full or partial refund."""

    @abstractmethod
    async def get_payment(self, payment_intent_id: str) -> PaymentIntent:
        """Retrieve the current state of a payment intent."""
