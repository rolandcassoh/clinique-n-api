"""Cas d'utilisation du module portefeuille."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.portefeuille.domain.entites import PatientWallet, WalletHistory
from app.modules.portefeuille.domain.exceptions import InsufficientFundsError, WalletNotFoundError
from app.modules.portefeuille.domain.depots import WalletRepository
from app.shared.schemas.pagination import Page, PaginationParams


class GetMyWalletUseCase:
    def __init__(self, repo: WalletRepository) -> None:
        self._repo = repo

    async def execute(self, id_utilisateur: int) -> PatientWallet:
        return await self._repo.find_by_user_or_create(id_utilisateur)


class GetWalletHistoryUseCase:
    def __init__(self, repo: WalletRepository) -> None:
        self._repo = repo

    async def execute(self, id_utilisateur: int, params: PaginationParams) -> Page:
        wallet = await self._repo.find_by_user_or_create(id_utilisateur)
        history, total = await self._repo.get_history(wallet.id, params)
        return Page.create(history, total, params)


class TopUpWalletUseCase:
    def __init__(self, repo: WalletRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_utilisateur: int,
        montant: Decimal,
        passerelle: str,
        reference: Optional[str] = None,
    ) -> PatientWallet:
        wallet = await self._repo.find_by_user_or_create(id_utilisateur)
        transaction = wallet.credit(
            montant,
            description=f"Rechargement via {passerelle}",
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

    async def execute(self, id_utilisateur: int, id_rendez_vous: int, montant: Decimal) -> PatientWallet:
        """Débite le wallet atomiquement. Lève InsufficientFundsError si solde insuffisant."""
        wallet = await self._wallet_repo.find_by_user(id_utilisateur)
        if wallet is None:
            raise WalletNotFoundError(id_utilisateur)

        transaction = wallet.debit(
            montant,
            description=f"Paiement RDV #{id_rendez_vous}",
            reference=f"APT-{id_rendez_vous}",
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

    async def execute(self, id_utilisateur: int) -> PatientWallet:
        wallet = await self._repo.find_by_user(id_utilisateur)
        if wallet is None:
            raise WalletNotFoundError(id_utilisateur)
        return wallet
