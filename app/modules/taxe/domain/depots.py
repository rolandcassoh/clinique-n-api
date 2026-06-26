"""Interface abstraite du repository tax."""
from abc import ABC, abstractmethod
from decimal import Decimal

from app.modules.taxe.domain.entites import Tax


class AbstractTaxRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[Tax]:
        """Retourne toutes les taxes actives et non supprimées."""
        ...

    @abstractmethod
    async def get_default(self) -> Tax | None:
        """Retourne la taxe par défaut active, ou None."""
        ...

    @abstractmethod
    async def get_by_id(self, id_taxe: int) -> Tax | None:
        """Retourne une taxe par son identifiant, ou None."""
        ...

    @abstractmethod
    async def create(
        self,
        nom: str,
        tarif: Decimal,
        type: str,
        id_pays: int | None,
        est_defaut: bool,
        est_actif: bool,
    ) -> Tax:
        """Crée et persiste une nouvelle taxe."""
        ...

    @abstractmethod
    async def update(
        self,
        id_taxe: int,
        nom: str,
        tarif: Decimal,
        type: str,
        id_pays: int | None,
        est_defaut: bool,
        est_actif: bool,
    ) -> Tax | None:
        """Met à jour une taxe existante. Retourne None si introuvable."""
        ...

    @abstractmethod
    async def set_default(self, id_taxe: int) -> Tax:
        """
        Opération atomique : remet est_defaut=false sur toutes les taxes,
        puis est_defaut=true sur id_taxe — dans la même transaction.
        """
        ...

    @abstractmethod
    async def soft_delete(self, id_taxe: int) -> bool:
        """Suppression douce : positionne deleted_at. Retourne True si effectuée."""
        ...
