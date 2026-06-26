"""Entités du domaine — module abonnements. Aucun import FastAPI/SQLAlchemy."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional


@dataclass
class PlanLimitation:
    id: int
    id_plan: int
    fonctionnalite: str
    valeur: str
    created_at: datetime
    updated_at: datetime


@dataclass
class SubscriptionPlan:
    id: int
    nom: str
    identifiant_url: str
    description: Optional[str]
    prix: Decimal
    periode_facturation: str  # 'monthly' | 'yearly' (mensuel ou annuel)
    jours_essai: int
    est_actif: bool
    est_mis_en_avant: bool
    ordre_affichage: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    limitations: list[PlanLimitation] = field(default_factory=list)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def period_days(self) -> int:
        """Retourne le nombre de jours correspondant à la période de facturation."""
        return 365 if self.periode_facturation == "yearly" else 30


@dataclass
class Subscription:
    id: int
    id_clinique: int
    id_plan: int
    statut: str  # 'trial' | 'active' | 'cancelled' | 'expired' (statut de l'abonnement)
    debut_le: datetime
    fin_le: datetime
    renouvellement_auto: bool
    annule_le: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_active_or_trial(self) -> bool:
        return self.statut in ("active", "trial")

    def cancel(self, now: datetime) -> None:
        self.renouvellement_auto = False
        self.statut = "cancelled"
        self.annule_le = now

    def renew(self, now: datetime, period_days: int) -> None:
        """Renouvelle l'abonnement. Nouvelle date de fin = max(maintenant, fin actuelle) + période."""
        base = max(now, self.fin_le)
        self.fin_le = base + timedelta(days=period_days)
        self.statut = "active"
        self.renouvellement_auto = True
