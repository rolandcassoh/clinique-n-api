"""Implémentation SQLAlchemy asynchrone du repository devise (devise)."""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.devise.domain.entites import Currency
from app.modules.devise.domain.depots import AbstractCurrencyRepository
from app.modules.devise.infrastructure.modeles import CurrencyModel


def _to_entity(m: CurrencyModel) -> Currency:
    return Currency(
        id=m.id, nom=m.nom, code=m.code, symbole=m.symbole,
        taux_change=m.taux_change, est_defaut=m.est_defaut, est_actif=m.est_actif,
    )


class SQLCurrencyRepository(AbstractCurrencyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[Currency]:
        requete = select(CurrencyModel).where(
            CurrencyModel.est_actif.is_(True),
            CurrencyModel.deleted_at.is_(None),
        )
        resultat = await self._session.execute(requete)
        return [_to_entity(ligne) for ligne in resultat.scalars().all()]

    async def get_default(self) -> Currency | None:
        requete = select(CurrencyModel).where(
            CurrencyModel.est_defaut.is_(True),
            CurrencyModel.deleted_at.is_(None),
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def get_by_code(self, code: str) -> Currency | None:
        requete = select(CurrencyModel).where(
            CurrencyModel.code == code,
            CurrencyModel.deleted_at.is_(None),
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def get_by_id(self, currency_id: int) -> Currency | None:
        requete = select(CurrencyModel).where(
            CurrencyModel.id == currency_id,
            CurrencyModel.deleted_at.is_(None),
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def create(
        self, nom: str, code: str, symbole: str, taux_change: Decimal,
        est_defaut: bool, est_actif: bool
    ) -> Currency:
        modele = CurrencyModel(
            nom=nom, code=code, symbole=symbole,
            taux_change=taux_change, est_defaut=est_defaut, est_actif=est_actif,
        )
        self._session.add(modele)
        await self._session.flush()
        await self._session.refresh(modele)
        return _to_entity(modele)

    async def update(
        self, currency_id: int, nom: str, code: str, symbole: str,
        taux_change: Decimal, est_defaut: bool, est_actif: bool
    ) -> Currency | None:
        requete = (
            update(CurrencyModel)
            .where(CurrencyModel.id == currency_id, CurrencyModel.deleted_at.is_(None))
            .values(
                nom=nom, code=code, symbole=symbole,
                taux_change=taux_change, est_defaut=est_defaut, est_actif=est_actif,
            )
            .returning(CurrencyModel)
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def set_default(self, currency_id: int) -> Currency | None:
        # Vérifier que la devise existe avant de modifier les autres
        cible = await self.get_by_id(currency_id)
        if cible is None:
            return None

        # Remettre toutes les devises à est_defaut=False dans la même transaction
        await self._session.execute(
            update(CurrencyModel)
            .where(CurrencyModel.deleted_at.is_(None))
            .values(est_defaut=False)
        )
        requete = (
            update(CurrencyModel)
            .where(CurrencyModel.id == currency_id)
            .values(est_defaut=True)
            .returning(CurrencyModel)
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None
