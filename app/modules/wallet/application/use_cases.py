"""Cas d'utilisation du module wallet."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.wallet.domain.entities import PatientWallet, WalletHistory
from app.modules.wallet.domain.exceptions import InsufficientFundsError, WalletNotFoundError
from app.modules.wallet.domain.repositories import WalletRepository
from app.shared.schemas.pagination import Page, PaginationParams


class GetMyWalletUseCase:
    def __init__(self, repo: WalletRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: int) -> PatientWallet:
        return await self._repo.find_by_user_or_create(user_id)


class GetWalletHistoryUseCase:
    def __init__(self, repo: WalletRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: int, params: PaginationParams) -> Page:
        wallet = await self._repo.find_by_user_or_create(user_id)
        history, total = await self._repo.get_history(wallet.id, params)
        return Page.create(history, total, params)


class TopUpWalletUseCase:
    def __init__(self, repo: WalletRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        user_id: int,
        amount: Decimal,
        gateway: str,
        reference: Optional[str] = None,
    ) -> PatientWallet:
        wallet = await self._repo.find_by_user_or_create(user_id)
        transaction = wallet.credit(
            amount,
            description=f"Rechargement via {gateway}",
            reference=reference,
        )
        await self._repo.save(wallet)
        await self._repo.record_transaction(wallet.id, transaction)
        return wallet


class PayAppointmentWithWalletUseCase:
    """Paiement atomique d'un RDV avec le portefeuille patient."""

    def __init__(
        self,
        wallet_repo: WalletRepository,
        session: AsyncSession,
    ) -> None:
        self._wallet_repo = wallet_repo
        self._session = session

    async def execute(self, user_id: int, appointment_id: int, amount: Decimal) -> PatientWallet:
        """Débite le wallet atomiquement. Lève InsufficientFundsError si solde insuffisant."""
        wallet = await self._wallet_repo.find_by_user(user_id)
        if wallet is None:
            raise WalletNotFoundError(user_id)

        transaction = wallet.debit(
            amount,
            description=f"Paiement RDV #{appointment_id}",
            reference=f"APT-{appointment_id}",
        )
        await self._wallet_repo.save(wallet)
        await self._wallet_repo.record_transaction(wallet.id, transaction)
        return wallet


class AdminListWalletsUseCase:
    def __init__(self, repo: WalletRepository) -> None:
        self._repo = repo

    async def execute(self, params: PaginationParams) -> Page:
        wallets, total = await self._repo.list_all(params)
        return Page.create(wallets, total, params)


class AdminGetWalletUseCase:
    def __init__(self, repo: WalletRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: int) -> PatientWallet:
        wallet = await self._repo.find_by_user(user_id)
        if wallet is None:
            raise WalletNotFoundError(user_id)
        return wallet
