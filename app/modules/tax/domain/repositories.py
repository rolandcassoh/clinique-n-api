from abc import ABC, abstractmethod
from decimal import Decimal

from app.modules.tax.domain.entities import Tax


class AbstractTaxRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[Tax]:
        ...

    @abstractmethod
    async def get_default(self) -> Tax | None:
        ...

    @abstractmethod
    async def get_by_id(self, tax_id: int) -> Tax | None:
        ...

    @abstractmethod
    async def create(
        self,
        name: str,
        rate: Decimal,
        type: str,
        country_id: int | None,
        is_default: bool,
        is_active: bool,
    ) -> Tax:
        ...

    @abstractmethod
    async def update(
        self,
        tax_id: int,
        name: str,
        rate: Decimal,
        type: str,
        country_id: int | None,
        is_default: bool,
        is_active: bool,
    ) -> Tax | None:
        ...

    @abstractmethod
    async def set_default(self, tax_id: int) -> Tax:
        """
        Reset is_default=false sur toutes les taxes,
        puis is_default=true sur tax_id — tout dans une seule transaction.
        """
        ...

    @abstractmethod
    async def soft_delete(self, tax_id: int) -> bool:
        ...
