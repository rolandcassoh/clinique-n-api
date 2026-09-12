"""Implémentation SQLAlchemy asynchrone du repository promotion."""
import math
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.promotion.domain.entites import Promotion, PromotionUse
from app.modules.promotion.domain.depots import AbstractPromotionRepository
from app.modules.promotion.infrastructure.modeles import PromotionModel, PromotionUseModel
from app.shared.schemas.pagination import Page, PaginationParams


def _to_entity(m: PromotionModel) -> Promotion:
    return Promotion(
        id=m.id,
        code=m.code,
        nom=m.nom,
        type=m.type,
        valeur=m.valeur,
        montant_min_commande=m.montant_min_commande,
        remise_maximale=m.remise_maximale,
        limite_utilisation=m.limite_utilisation,
        compteur_utilisation=m.compteur_utilisation,
        debut_le=m.debut_le,
        expire_le=m.expire_le,
        est_actif=m.est_actif,
        applicable_a=m.applicable_a,
        created_at=m.created_at,
        deleted_at=m.deleted_at,
    )


def _use_to_entity(m: PromotionUseModel) -> PromotionUse:
    return PromotionUse(
        id=m.id,
        id_promotion=m.id_promotion,
        id_utilisateur=m.id_utilisateur,
        id_commande=m.id_commande,
        id_rendez_vous=m.id_rendez_vous,
        montant_remise=m.montant_remise,
        utilise_le=m.utilise_le,
        created_at=m.created_at,
    )


class SQLPromotionRepository(AbstractPromotionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, params: PaginationParams) -> Page[Promotion]:
        requete_compte = select(func.count()).select_from(PromotionModel).where(
            PromotionModel.deleted_at.is_(None)
        )
        resultat_total = await self._session.execute(requete_compte)
        total = resultat_total.scalar_one()

        requete = (
            select(PromotionModel)
            .where(PromotionModel.deleted_at.is_(None))
            .order_by(PromotionModel.id.desc())
            .offset(params.offset)
            .limit(params.per_page)
        )
        resultat = await self._session.execute(requete)
        elements = [_to_entity(modele) for modele in resultat.scalars().all()]
        return Page.create(data=elements, total=total, params=params)

    async def get_by_id(self, id_promotion: int) -> Promotion | None:
        requete = select(PromotionModel).where(PromotionModel.id == id_promotion)
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def get_by_code(self, code: str) -> Promotion | None:
        requete = select(PromotionModel).where(PromotionModel.code == code)
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

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
        modele = PromotionModel(
            code=code,
            nom=nom,
            type=type,
            valeur=valeur,
            montant_min_commande=montant_min_commande,
            remise_maximale=remise_maximale,
            limite_utilisation=limite_utilisation,
            compteur_utilisation=0,
            debut_le=debut_le,
            expire_le=expire_le,
            est_actif=est_actif,
            applicable_a=applicable_a,
        )
        self._session.add(modele)
        await self._session.flush()
        await self._session.refresh(modele)
        return _to_entity(modele)

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
        # MySQL ne supporte pas UPDATE ... RETURNING (syntaxe Postgres) : on met à jour
        # puis on relit la ligne.
        requete = (
            update(PromotionModel)
            .where(
                PromotionModel.id == id_promotion,
                PromotionModel.deleted_at.is_(None),
            )
            .values(
                code=code,
                nom=nom,
                type=type,
                valeur=valeur,
                montant_min_commande=montant_min_commande,
                remise_maximale=remise_maximale,
                limite_utilisation=limite_utilisation,
                debut_le=debut_le,
                expire_le=expire_le,
                est_actif=est_actif,
                applicable_a=applicable_a,
            )
        )
        resultat = await self._session.execute(requete)
        if resultat.rowcount == 0:
            return None
        modele = (
            await self._session.execute(
                select(PromotionModel).where(PromotionModel.id == id_promotion)
            )
        ).scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def soft_delete(self, id_promotion: int) -> bool:
        requete = (
            update(PromotionModel)
            .where(
                PromotionModel.id == id_promotion,
                PromotionModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        resultat = await self._session.execute(requete)
        return resultat.rowcount > 0

    async def list_uses(
        self, id_promotion: int, params: PaginationParams
    ) -> Page[PromotionUse]:
        requete_compte = select(func.count()).select_from(PromotionUseModel).where(
            PromotionUseModel.id_promotion == id_promotion
        )
        resultat_total = await self._session.execute(requete_compte)
        total = resultat_total.scalar_one()

        requete = (
            select(PromotionUseModel)
            .where(PromotionUseModel.id_promotion == id_promotion)
            .order_by(PromotionUseModel.utilise_le.desc())
            .offset(params.offset)
            .limit(params.per_page)
        )
        resultat = await self._session.execute(requete)
        elements = [_use_to_entity(modele) for modele in resultat.scalars().all()]
        return Page.create(data=elements, total=total, params=params)
