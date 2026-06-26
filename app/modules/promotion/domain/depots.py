from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from app.modules.promotion.domain.entites import Promotion, PromotionUse
from app.shared.schemas.pagination import Page, PaginationParams


class AbstractPromotionRepository(ABC):
    @abstractmethod
    async def list(self, params: PaginationParams) -> Page[Promotion]:
        ...

    @abstractmethod
    async def get_by_id(self, id_promotion: int) -> Promotion | None:
        ...

    @abstractmethod
    async def get_by_code(self, code: str) -> Promotion | None:
        ...

    @abstractmethod
    async def create(
        self,
        code: str,
        nom: str,
        type: str,
        valeur: Decimal,
        montant_min_commande: Decimal | None,
        remise_maximale: Decimal | None,
        limite_utilisation: int | None,
        debut_le: datetime | None,
        expire_le: datetime | None,
        est_actif: bool,
        applicable_a: str,
    ) -> Promotion:
        ...

    @abstractmethod
    async def update(
        self,
        id_promotion: int,
        code: str,
        nom: str,
        type: str,
        valeur: Decimal,
        montant_min_commande: Decimal | None,
        remise_maximale: Decimal | None,
        limite_utilisation: int | None,
        debut_le: datetime | None,
        expire_le: datetime | None,
        est_actif: bool,
        applicable_a: str,
    ) -> Promotion | None:
        ...

    @abstractmethod
    async def soft_delete(self, id_promotion: int) -> bool:
        ...

    @abstractmethod
    async def list_uses(self, id_promotion: int, params: PaginationParams) -> Page[PromotionUse]:
        ...
