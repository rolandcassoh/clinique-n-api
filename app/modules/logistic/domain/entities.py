"""Entités domaine Logistic — pur Python, aucune dépendance externe."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class ShippingZone:
    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def __str__(self) -> str:
        return f"ShippingZone({self.id}: {self.name})"


@dataclass
class ShippingRate:
    id: int
    zone_id: int
    name: str
    min_weight: Decimal
    max_weight: Decimal | None
    min_order_amount: Decimal
    rate: Decimal
    is_free_shipping: bool
    estimated_days_min: int
    estimated_days_max: int
    is_active: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_applicable_for_amount(self, amount: Decimal) -> bool:
        """Vérifie si ce tarif est applicable pour un montant de commande donné."""
        return self.is_active and self.min_order_amount <= amount

    def __str__(self) -> str:
        return f"ShippingRate({self.id}: {self.name}, zone={self.zone_id})"


@dataclass
class ShippingCalculationResult:
    """Résultat du calcul de frais de livraison."""
    rate: Decimal
    estimated_days_min: int
    estimated_days_max: int
    rate_name: str
    is_free_shipping: bool
