from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PaymentIntent:
    id: str
    montant: Decimal
    devise: str
    statut: str
    client_secret: str | None = None


@dataclass
class RefundResult:
    id: str
    montant: Decimal
    statut: str


class PaymentPort(ABC):
    @abstractmethod
    async def create_payment_intent(
        self,
        montant: Decimal,
        devise: str,
        metadata: dict[str, str] | None = None,
    ) -> PaymentIntent:
        """Crée une intention de paiement et la retourne."""

    @abstractmethod
    async def confirm_payment(self, payment_intent_id: str) -> PaymentIntent:
        """Confirme une intention de paiement existante."""

    @abstractmethod
    async def refund(self, payment_intent_id: str, montant: Decimal | None = None) -> RefundResult:
        """Émet un remboursement total ou partiel."""

    @abstractmethod
    async def get_payment(self, payment_intent_id: str) -> PaymentIntent:
        """Récupère l'état courant d'une intention de paiement."""
