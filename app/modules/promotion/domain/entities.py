from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class Promotion:
    id: int
    code: str
    name: str
    type: str  # 'percentage' | 'fixed'
    value: Decimal
    min_order_amount: Decimal | None
    max_discount_amount: Decimal | None
    usage_limit: int | None
    usage_count: int
    starts_at: datetime | None
    expires_at: datetime | None
    is_active: bool
    applicable_to: str  # 'all' | 'products' | 'services' | 'appointments'
    created_at: datetime
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def is_valid_at(self, now: datetime) -> bool:
        """Vérifie si la promo est dans sa période de validité."""
        def _as_naive(dt: datetime) -> datetime:
            """Normalise en naive UTC pour une comparaison homogène."""
            if dt.tzinfo is not None:
                return dt.replace(tzinfo=None)
            return dt

        now_naive = _as_naive(now)
        if self.starts_at and now_naive < _as_naive(self.starts_at):
            return False
        if self.expires_at and now_naive > _as_naive(self.expires_at):
            return False
        return True

    def has_remaining_uses(self) -> bool:
        if self.usage_limit is None:
            return True
        return self.usage_count < self.usage_limit

    def is_applicable_to(self, context: str) -> bool:
        return self.applicable_to == "all" or self.applicable_to == context

    def calculate_discount(self, amount: Decimal) -> Decimal:
        if self.type == "percentage":
            discount = amount * self.value / Decimal("100")
            if self.max_discount_amount is not None:
                discount = min(discount, self.max_discount_amount)
        else:  # fixed
            discount = min(self.value, amount)
        return discount


@dataclass
class PromotionUse:
    id: int
    promotion_id: int
    user_id: int
    order_id: int | None
    appointment_id: int | None
    discount_amount: Decimal
    used_at: datetime
    created_at: datetime


@dataclass
class ValidationResult:
    valid: bool
    discount_amount: Decimal
    promotion: Promotion | None
    reason: str | None = None
