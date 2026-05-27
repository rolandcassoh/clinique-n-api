"""Domain entities — module subscription. Zéro import FastAPI/SQLAlchemy."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional


@dataclass
class PlanLimitation:
    id: int
    plan_id: int
    feature: str
    value: str
    created_at: datetime
    updated_at: datetime


@dataclass
class SubscriptionPlan:
    id: int
    name: str
    slug: str
    description: Optional[str]
    price: Decimal
    billing_period: str  # 'monthly' | 'yearly'
    trial_days: int
    is_active: bool
    is_featured: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    limitations: list[PlanLimitation] = field(default_factory=list)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def period_days(self) -> int:
        """Nombre de jours pour la période de facturation."""
        return 365 if self.billing_period == "yearly" else 30


@dataclass
class Subscription:
    id: int
    clinic_id: int
    plan_id: int
    status: str  # 'trial' | 'active' | 'cancelled' | 'expired'
    starts_at: datetime
    ends_at: datetime
    auto_renew: bool
    cancelled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_active_or_trial(self) -> bool:
        return self.status in ("active", "trial")

    def cancel(self, now: datetime) -> None:
        self.auto_renew = False
        self.status = "cancelled"
        self.cancelled_at = now

    def renew(self, now: datetime, period_days: int) -> None:
        """Renouvelle l'abonnement. Nouvelle ends_at = max(now, ends_at) + période."""
        base = max(now, self.ends_at)
        self.ends_at = base + timedelta(days=period_days)
        self.status = "active"
        self.auto_renew = True
