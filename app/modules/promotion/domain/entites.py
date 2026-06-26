"""Entités domaine promotion — aucune dépendance externe."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class Promotion:
    id: int
    code: str
    nom: str
    type: str  # 'percentage' | 'fixed'
    valeur: Decimal
    montant_min_commande: Decimal | None
    remise_maximale: Decimal | None
    limite_utilisation: int | None
    compteur_utilisation: int
    debut_le: datetime | None
    expire_le: datetime | None
    est_actif: bool
    applicable_a: str  # 'all' | 'products' | 'services' | 'appointments'
    created_at: datetime
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def is_valid_at(self, now: datetime) -> bool:
        """Vérifie si la promotion est dans sa période de validité."""
        def _as_naive(dt: datetime) -> datetime:
            """Normalise en naive UTC pour une comparaison homogène."""
            if dt.tzinfo is not None:
                return dt.replace(tzinfo=None)
            return dt

        now_naive = _as_naive(now)
        if self.debut_le and now_naive < _as_naive(self.debut_le):
            return False
        if self.expire_le and now_naive > _as_naive(self.expire_le):
            return False
        return True

    def has_remaining_uses(self) -> bool:
        if self.limite_utilisation is None:
            return True
        return self.compteur_utilisation < self.limite_utilisation

    def is_applicable_to(self, context: str) -> bool:
        return self.applicable_a == "all" or self.applicable_a == context

    def calculate_discount(self, montant: Decimal) -> Decimal:
        """Calcule le montant de remise applicable."""
        if self.type == "percentage":
            remise = montant * self.valeur / Decimal("100")
            if self.remise_maximale is not None:
                remise = min(remise, self.remise_maximale)
        else:  # fixed
            remise = min(self.valeur, montant)
        return remise


@dataclass
class PromotionUse:
    id: int
    id_promotion: int
    id_utilisateur: int
    id_commande: int | None
    id_rendez_vous: int | None
    montant_remise: Decimal
    utilise_le: datetime
    created_at: datetime


@dataclass
class ValidationResult:
    valid: bool
    montant_remise: Decimal
    promotion: Promotion | None
    motif: str | None = None
