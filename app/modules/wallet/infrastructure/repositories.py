"""Implémentations SQLAlchemy async des repositories wallet."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.wallet.domain.entities import (
    PatientWallet,
    WalletHistory,
    WalletTransaction,
)
from app.modules.wallet.domain.repositories import WalletRepository
from app.modules.wallet.infrastructure.models import PatientWalletModel, WalletHistoryModel
from app.shared.schemas.pagination import PaginationParams


def _wallet_to_entity(m: PatientWalletModel) -> PatientWallet:
    return PatientWallet(
        id=m.id,
        user_id=m.user_id,
        balance=Decimal(str(m.balance)),
        currency=m.currency,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _history_to_entity(m: WalletHistoryModel) -> WalletHistory:
    return WalletHistory(
        id=m.id,
        wallet_id=m.wallet_id,
        amount=Decimal(str(m.amount)),
        type=m.type,
        reference=m.reference,
        description=m.description,
        balance_after=Decimal(str(m.balance_after)),
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyWalletRepository(WalletRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_user(self, user_id: int) -> Optional[PatientWallet]:
        q = select(PatientWalletModel).where(
            PatientWalletModel.user_id == user_id,
            PatientWalletModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _wallet_to_entity(row) if row else None

    async def find_by_user_or_create(self, user_id: int) -> PatientWallet:
        wallet = await self.find_by_user(user_id)
        if wallet is not None:
            return wallet
        # Créer un wallet avec solde 0
        model = PatientWalletModel(user_id=user_id, balance=Decimal("0"), currency="XAF")
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _wallet_to_entity(model)

    async def save(self, wallet: PatientWallet) -> PatientWallet:
        q = select(PatientWalletModel).where(PatientWalletModel.id == wallet.id)
        row = (await self._session.execute(q)).scalar_one()
        row.balance = wallet.balance
        await self._session.flush()
        await self._session.refresh(row)
        return _wallet_to_entity(row)

    async def record_transaction(
        self, wallet_id: int, transaction: WalletTransaction
    ) -> WalletHistory:
        hist = WalletHistoryModel(
            wallet_id=wallet_id,
            amount=transaction.amount,
            type=transaction.type,
            reference=transaction.reference,
            description=transaction.description,
            balance_after=transaction.balance_after,
        )
        self._session.add(hist)
        await self._session.flush()
        await self._session.refresh(hist)
        return _history_to_entity(hist)

    async def get_history(
        self, wallet_id: int, params: PaginationParams
    ) -> tuple[list[WalletHistory], int]:
        base = select(WalletHistoryModel).where(
            WalletHistoryModel.wallet_id == wallet_id
        )
        total: int = (
            await self._session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (
            await self._session.execute(
                base.order_by(WalletHistoryModel.created_at.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_history_to_entity(r) for r in rows], total

    async def list_all(
        self, params: PaginationParams
    ) -> tuple[list[PatientWallet], int]:
        base = select(PatientWalletModel).where(
            PatientWalletModel.deleted_at.is_(None)
        )
        total: int = (
            await self._session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (
            await self._session.execute(
                base.order_by(PatientWalletModel.id.asc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_wallet_to_entity(r) for r in rows], total
