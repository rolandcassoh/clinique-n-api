"""Implémentation SQLAlchemy asynchrone du repository tax."""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.taxe.domain.entites import Tax
from app.modules.taxe.domain.depots import AbstractTaxRepository
from app.modules.taxe.infrastructure.modeles import TaxModel


def _to_entity(modele: TaxModel) -> Tax:
    return Tax(
        id=modele.id,
        nom=modele.nom,
        tarif=modele.tarif,
        type=modele.type,
        id_pays=modele.id_pays,
        est_defaut=modele.est_defaut,
        est_actif=modele.est_actif,
        created_at=modele.created_at,
        deleted_at=modele.deleted_at,
    )


class SQLTaxRepository(AbstractTaxRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[Tax]:
        requete = select(TaxModel).where(
            TaxModel.deleted_at.is_(None),
            TaxModel.est_actif.is_(True),
        ).order_by(TaxModel.nom)
        resultat = await self._session.execute(requete)
        return [_to_entity(modele) for modele in resultat.scalars().all()]

    async def get_default(self) -> Tax | None:
        requete = select(TaxModel).where(
            TaxModel.deleted_at.is_(None),
            TaxModel.est_actif.is_(True),
            TaxModel.est_defaut.is_(True),
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def get_by_id(self, id_taxe: int) -> Tax | None:
        requete = select(TaxModel).where(TaxModel.id == id_taxe)
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def create(
        self,
        nom: str,
        tarif: Decimal,
        type: str,
        id_pays: int | None,
        est_defaut: bool,
        est_actif: bool,
    ) -> Tax:
        modele = TaxModel(
            nom=nom,
            tarif=tarif,
            type=type,
            id_pays=id_pays,
            est_defaut=est_defaut,
            est_actif=est_actif,
        )
        self._session.add(modele)
        await self._session.flush()
        await self._session.refresh(modele)
        return _to_entity(modele)

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
        # MySQL ne supporte pas UPDATE ... RETURNING (syntaxe Postgres) : on met à jour
        # puis on relit la ligne.
        requete = (
            update(TaxModel)
            .where(TaxModel.id == id_taxe, TaxModel.deleted_at.is_(None))
            .values(
                nom=nom,
                tarif=tarif,
                type=type,
                id_pays=id_pays,
                est_defaut=est_defaut,
                est_actif=est_actif,
            )
        )
        resultat = await self._session.execute(requete)
        if resultat.rowcount == 0:
            return None
        modele = (
            await self._session.execute(select(TaxModel).where(TaxModel.id == id_taxe))
        ).scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def set_default(self, id_taxe: int) -> Tax:
        """
        Opération atomique : remet est_defaut=false sur toutes les taxes puis positionne la cible.
        La session parente gère la transaction (via get_db).
        """
        # 1. Réinitialiser est_defaut sur toutes les taxes non supprimées
        requete_reset = (
            update(TaxModel)
            .where(TaxModel.deleted_at.is_(None))
            .values(est_defaut=False)
        )
        await self._session.execute(requete_reset)

        # 2. Positionner est_defaut=true sur la taxe cible
        requete_set = (
            update(TaxModel)
            .where(TaxModel.id == id_taxe, TaxModel.deleted_at.is_(None))
            .values(est_defaut=True)
        )
        await self._session.execute(requete_set)
        modele = (
            await self._session.execute(select(TaxModel).where(TaxModel.id == id_taxe))
        ).scalar_one()
        return _to_entity(modele)

    async def soft_delete(self, id_taxe: int) -> bool:
        requete = (
            update(TaxModel)
            .where(TaxModel.id == id_taxe, TaxModel.deleted_at.is_(None))
            .values(deleted_at=datetime.now(timezone.utc))
        )
        resultat = await self._session.execute(requete)
        return resultat.rowcount > 0
