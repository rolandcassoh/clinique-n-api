"""ABCs (ports) des repositories wallet."""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from app.modules.wallet.domain.entities import PatientWallet, WalletHistory, WalletTransaction
from app.shared.schemas.pagination import PaginationParams


class WalletRepository(ABC):
    @abstractmethod
    async def find_by_user(self, user_id: int) -> Optional[PatientWallet]: ...

    @abstractmethod
    async def find_by_user_or_create(self, user_id: int) -> PatientWallet: ...

    @abstractmethod
    async def save(self, wallet: PatientWallet) -> PatientWallet: ...

    @abstractmethod
    async def record_transaction(
        self, wallet_id: int, transaction: WalletTransaction
    ) -> WalletHistory: ...

    @abstractmethod
    async def get_history(
        self, wallet_id: int, params: PaginationParams
    ) -> tuple[list[WalletHistory], int]: ...

    @abstractmethod
    async def list_all(
        self, params: PaginationParams
    ) -> tuple[list[PatientWallet], int]: ...
