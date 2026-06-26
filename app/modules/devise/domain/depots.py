"""Interface (ABC) du repository devise (devise)."""
from abc import ABC, abstractmethod
from decimal import Decimal

from app.modules.devise.domain.entites import Currency


class AbstractCurrencyRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[Currency]:
        """Retourne toutes les devises actives."""
        ...

    @abstractmethod
    async def get_default(self) -> Currency | None:
        """Retourne la devise par défaut ou None."""
        ...

    @abstractmethod
    async def get_by_code(self, code: str) -> Currency | None:
        """Retourne une devise par son code ISO ou None."""
        ...

    @abstractmethod
    async def get_by_id(self, currency_id: int) -> Currency | None:
        """Retourne une devise par son id ou None."""
        ...

    @abstractmethod
    async def create(
        self, nom: str, code: str, symbole: str, taux_change: Decimal,
        est_defaut: bool, est_actif: bool
    ) -> Currency:
        """Crée et retourne une nouvelle devise."""
        ...

    @abstractmethod
    async def update(
        self, currency_id: int, nom: str, code: str, symbole: str,
        taux_change: Decimal, est_defaut: bool, est_actif: bool
    ) -> Currency | None:
        """Met à jour une devise, retourne None si inexistante."""
        ...

    @abstractmethod
    async def set_default(self, currency_id: int) -> Currency | None:
        """Remet toutes les devises à est_defaut=false, puis définit celle-ci par défaut."""
        ...
