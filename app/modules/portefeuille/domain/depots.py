"""ABCs (ports) des repositories wallet."""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from app.modules.portefeuille.domain.entites import PatientWallet, WalletHistory, WalletTransaction
from app.shared.schemas.pagination import PaginationParams


class WalletRepository(ABC):
    @abstractmethod
    async def find_by_user(self, id_utilisateur: int) -> Optional[PatientWallet]: ...

    @abstractmethod
    async def find_by_user_or_create(self, id_utilisateur: int) -> PatientWallet: ...

    @abstractmethod
    async def save(self, wallet: PatientWallet) -> PatientWallet: ...

    @abstractmethod
    async def record_transaction(
        self, id_portefeuille: int, transaction: WalletTransaction
    ) -> WalletHistory: ...

    @abstractmethod
    async def get_history(
        self, id_portefeuille: int, params: PaginationParams
    ) -> tuple[list[WalletHistory], int]: ...

    @abstractmethod
    async def list_all(
        self, params: PaginationParams
    ) -> tuple[list[PatientWallet], int]: ...
