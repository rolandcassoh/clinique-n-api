"""Entités domaine Logistic — pur Python, aucune dépendance externe."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class ShippingZone:
    id: int
    nom: str
    description: str | None
    est_actif: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def deactivate(self) -> None:
        self.est_actif = False

    def activate(self) -> None:
        self.est_actif = True

    def __str__(self) -> str:
        return f"ShippingZone({self.id}: {self.nom})"


@dataclass
class ShippingRate:
    id: int
    id_zone: int
    nom: str
    poids_min: Decimal
    poids_max: Decimal | None
    montant_min_commande: Decimal
    tarif: Decimal
    livraison_gratuite: bool
    jours_livraison_min: int
    jours_livraison_max: int
    est_actif: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_applicable_for_amount(self, montant: Decimal) -> bool:
        """Vérifie si ce tarif est applicable pour un montant de commande donné."""
        return self.est_actif and self.montant_min_commande <= montant

    def __str__(self) -> str:
        return f"ShippingRate({self.id}: {self.nom}, zone={self.id_zone})"


@dataclass
class ShippingCalculationResult:
    """Résultat du calcul de frais de livraison."""
    tarif: Decimal
    jours_livraison_min: int
    jours_livraison_max: int
    rate_name: str
    livraison_gratuite: bool
