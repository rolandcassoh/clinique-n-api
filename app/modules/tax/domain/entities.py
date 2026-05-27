from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Tax:
    id: int
    name: str
    rate: Decimal
    type: str  # 'percentage' | 'fixed'
    country_id: int | None
    is_default: bool
    is_active: bool
    created_at: datetime
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
