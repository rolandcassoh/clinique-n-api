"""Dépôts SQLAlchemy — module abonnements."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.abonnement.domain.entites import (
    PlanLimitation,
    Subscription,
    SubscriptionPlan,
)
from app.modules.abonnement.domain.depots import (
    AbstractSubscriptionPlanRepository,
    AbstractSubscriptionRepository,
)
from app.modules.abonnement.infrastructure.modeles import (
    PlanLimitationModel,
    SubscriptionModel,
    SubscriptionPlanModel,
)
from app.shared.schemas.pagination import PaginationParams


# ── Convertisseurs modèle → entité ────────────────────────────────────────────

def _to_limitation(m: PlanLimitationModel) -> PlanLimitation:
    return PlanLimitation(
        id=m.id, id_plan=m.id_plan, fonctionnalite=m.fonctionnalite, valeur=m.valeur,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _to_plan(m: SubscriptionPlanModel, limitations: list[PlanLimitation] | None = None) -> SubscriptionPlan:
    return SubscriptionPlan(
        id=m.id, nom=m.nom, identifiant_url=m.identifiant_url, description=m.description,
        prix=m.prix, periode_facturation=m.periode_facturation, jours_essai=m.jours_essai,
        est_actif=m.est_actif, est_mis_en_avant=m.est_mis_en_avant, ordre_affichage=m.ordre_affichage,
        created_at=m.created_at, updated_at=m.updated_at, deleted_at=m.deleted_at,
        limitations=limitations or [],
    )


def _to_subscription(m: SubscriptionModel) -> Subscription:
    return Subscription(
        id=m.id, id_clinique=m.id_clinique, id_plan=m.id_plan,
        statut=m.statut, debut_le=m.debut_le, fin_le=m.fin_le,
        renouvellement_auto=m.renouvellement_auto, annule_le=m.annule_le,
        created_at=m.created_at, updated_at=m.updated_at, deleted_at=m.deleted_at,
    )


# ── SubscriptionPlanRepository ────────────────────────────────────────────────

class SQLSubscriptionPlanRepository(AbstractSubscriptionPlanRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _load_limitations(self, id_plan: int) -> list[PlanLimitation]:
        stmt = select(PlanLimitationModel).where(PlanLimitationModel.id_plan == id_plan)
        result = await self._session.execute(stmt)
        return [_to_limitation(m) for m in result.scalars().all()]

    async def list_active(self) -> list[SubscriptionPlan]:
        stmt = (
            select(SubscriptionPlanModel)
            .where(
                SubscriptionPlanModel.est_actif.is_(True),
                SubscriptionPlanModel.deleted_at.is_(None),
            )
            .order_by(SubscriptionPlanModel.ordre_affichage)
        )
        resultat = await self._session.execute(stmt)
        forfaits = []
        for m in resultat.scalars().all():
            limitations = await self._load_limitations(m.id)
            forfaits.append(_to_plan(m, limitations))
        return forfaits

    async def get_by_slug(self, identifiant_url: str) -> Optional[SubscriptionPlan]:
        stmt = select(SubscriptionPlanModel).where(
            SubscriptionPlanModel.identifiant_url == identifiant_url,
            SubscriptionPlanModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        if m is None:
            return None
        limitations = await self._load_limitations(m.id)
        return _to_plan(m, limitations)

    async def get_by_id(self, id_plan: int) -> Optional[SubscriptionPlan]:
        stmt = select(SubscriptionPlanModel).where(
            SubscriptionPlanModel.id == id_plan,
            SubscriptionPlanModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        if m is None:
            return None
        limitations = await self._load_limitations(m.id)
        return _to_plan(m, limitations)

    async def create(
        self,
        nom: str,
        identifiant_url: str,
        prix: float,
        periode_facturation: str = "monthly",
        description: Optional[str] = None,
        jours_essai: int = 0,
        est_mis_en_avant: bool = False,
        ordre_affichage: int = 0,
    ) -> SubscriptionPlan:
        m = SubscriptionPlanModel(
            nom=nom, identifiant_url=identifiant_url, prix=Decimal(str(prix)),
            periode_facturation=periode_facturation, description=description,
            jours_essai=jours_essai, est_mis_en_avant=est_mis_en_avant, ordre_affichage=ordre_affichage,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_plan(m)

    async def update(self, id_plan: int, **kwargs) -> Optional[SubscriptionPlan]:
        stmt = (
            update(SubscriptionPlanModel)
            .where(
                SubscriptionPlanModel.id == id_plan,
                SubscriptionPlanModel.deleted_at.is_(None),
            )
            .values(**kwargs)
            .returning(SubscriptionPlanModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        if m is None:
            return None
        limitations = await self._load_limitations(id_plan)
        return _to_plan(m, limitations)

    async def upsert_limitation(
        self, id_plan: int, fonctionnalite: str, valeur: str
    ) -> PlanLimitation:
        # Recherche d'une limitation existante
        stmt = select(PlanLimitationModel).where(
            PlanLimitationModel.id_plan == id_plan,
            PlanLimitationModel.fonctionnalite == fonctionnalite,
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        if m is not None:
            m.valeur = valeur
            await self._session.flush()
            await self._session.refresh(m)
        else:
            m = PlanLimitationModel(id_plan=id_plan, fonctionnalite=fonctionnalite, valeur=valeur)
            self._session.add(m)
            await self._session.flush()
            await self._session.refresh(m)
        return _to_limitation(m)

    async def delete_limitation(self, id_plan: int, fonctionnalite: str) -> bool:
        stmt = select(PlanLimitationModel).where(
            PlanLimitationModel.id_plan == id_plan,
            PlanLimitationModel.fonctionnalite == fonctionnalite,
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        if m is None:
            return False
        await self._session.delete(m)
        await self._session.flush()
        return True


# ── SubscriptionRepository ────────────────────────────────────────────────────

class SQLSubscriptionRepository(AbstractSubscriptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_paginated(
        self, params: PaginationParams
    ) -> tuple[list[Subscription], int]:
        base = select(SubscriptionModel).where(SubscriptionModel.deleted_at.is_(None))
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        data_stmt = base.order_by(SubscriptionModel.created_at.desc()).offset(params.offset).limit(params.per_page)
        result = await self._session.execute(data_stmt)
        return [_to_subscription(m) for m in result.scalars().all()], total

    async def get_by_id(self, subscription_id: int) -> Optional[Subscription]:
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.id == subscription_id,
            SubscriptionModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_subscription(m) if m else None

    async def get_active_for_clinic(self, id_clinique: int) -> Optional[Subscription]:
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.id_clinique == id_clinique,
            SubscriptionModel.deleted_at.is_(None),
            or_(
                SubscriptionModel.statut == "active",
                SubscriptionModel.statut == "trial",
            ),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_subscription(m) if m else None

    async def create(
        self,
        id_clinique: int,
        id_plan: int,
        statut: str,
        debut_le,
        fin_le,
        renouvellement_auto: bool = True,
    ) -> Subscription:
        m = SubscriptionModel(
            id_clinique=id_clinique, id_plan=id_plan, statut=statut,
            debut_le=debut_le, fin_le=fin_le, renouvellement_auto=renouvellement_auto,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_subscription(m)

    async def update(self, subscription_id: int, **kwargs) -> Optional[Subscription]:
        stmt = (
            update(SubscriptionModel)
            .where(
                SubscriptionModel.id == subscription_id,
                SubscriptionModel.deleted_at.is_(None),
            )
            .values(**kwargs)
            .returning(SubscriptionModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_subscription(m) if m else None
