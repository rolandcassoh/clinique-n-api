"""Implémentations SQLAlchemy async des repositories wallet."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.portefeuille.domain.entites import (
    PatientWallet,
    WalletHistory,
    WalletTransaction,
)
from app.modules.portefeuille.domain.depots import WalletRepository
from app.modules.portefeuille.infrastructure.modeles import PatientWalletModel, WalletHistoryModel
from app.shared.schemas.pagination import PaginationParams


def _wallet_to_entity(m: PatientWalletModel) -> PatientWallet:
    return PatientWallet(
        id=m.id,
        id_utilisateur=m.id_utilisateur,
        solde=Decimal(str(m.solde)),
        devise=m.devise,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _history_to_entity(m: WalletHistoryModel) -> WalletHistory:
    return WalletHistory(
        id=m.id,
        id_portefeuille=m.id_portefeuille,
        montant=Decimal(str(m.montant)),
        type=m.type,
        reference=m.reference,
        description=m.description,
        solde_apres=Decimal(str(m.solde_apres)),
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyWalletRepository(WalletRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_user(self, id_utilisateur: int) -> Optional[PatientWallet]:
        q = select(PatientWalletModel).where(
            PatientWalletModel.id_utilisateur == id_utilisateur,
            PatientWalletModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _wallet_to_entity(row) if row else None

    async def find_by_user_or_create(self, id_utilisateur: int) -> PatientWallet:
        wallet = await self.find_by_user(id_utilisateur)
        if wallet is not None:
            return wallet
        # Créer un wallet avec solde 0
        model = PatientWalletModel(id_utilisateur=id_utilisateur, solde=Decimal("0"), devise="XAF")
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _wallet_to_entity(model)

    async def save(self, wallet: PatientWallet) -> PatientWallet:
        q = select(PatientWalletModel).where(PatientWalletModel.id == wallet.id)
        row = (await self._session.execute(q)).scalar_one()
        row.solde = wallet.solde
        await self._session.flush()
        await self._session.refresh(row)
        return _wallet_to_entity(row)

    async def record_transaction(
        self, id_portefeuille: int, transaction: WalletTransaction
    ) -> WalletHistory:
        hist = WalletHistoryModel(
            id_portefeuille=id_portefeuille,
            montant=transaction.montant,
            type=transaction.type,
            reference=transaction.reference,
            description=transaction.description,
            solde_apres=transaction.solde_apres,
        )
        self._session.add(hist)
        await self._session.flush()
        await self._session.refresh(hist)
        return _history_to_entity(hist)

    async def get_history(
        self, id_portefeuille: int, params: PaginationParams
    ) -> tuple[list[WalletHistory], int]:
        base = select(WalletHistoryModel).where(
            WalletHistoryModel.id_portefeuille == id_portefeuille
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
