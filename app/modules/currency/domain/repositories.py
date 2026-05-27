from abc import ABC, abstractmethod
from decimal import Decimal

from app.modules.currency.domain.entities import Currency


class AbstractCurrencyRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[Currency]:
        ...

    @abstractmethod
    async def get_default(self) -> Currency | None:
        ...

    @abstractmethod
    async def get_by_code(self, code: str) -> Currency | None:
        ...

    @abstractmethod
    async def get_by_id(self, currency_id: int) -> Currency | None:
        ...

    @abstractmethod
    async def create(
        self, name: str, code: str, symbol: str, exchange_rate: Decimal,
        is_default: bool, is_active: bool
    ) -> Currency:
        ...

    @abstractmethod
    async def update(
        self, currency_id: int, name: str, code: str, symbol: str,
        exchange_rate: Decimal, is_default: bool, is_active: bool
    ) -> Currency | None:
        ...

    @abstractmethod
    async def set_default(self, currency_id: int) -> Currency | None:
        """Reset toutes les devises à is_default=false, puis met celle-ci à true."""
        ...
