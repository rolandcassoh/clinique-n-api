from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Currency:
    id: int
    name: str
    code: str
    symbol: str
    exchange_rate: Decimal
    is_default: bool
    is_active: bool

    def set_default(self) -> None:
        self.is_default = True

    def unset_default(self) -> None:
        self.is_default = False
