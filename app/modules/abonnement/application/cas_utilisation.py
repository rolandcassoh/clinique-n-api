"""Cas d'utilisation — module abonnements."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.modules.abonnement.domain.entites import Subscription, SubscriptionPlan
from app.modules.abonnement.domain.exceptions import (
    ActiveSubscriptionExistsError,
    CannotRenewCancelledError,
    PlanLimitationNotFoundError,
    SubscriptionNotFoundError,
    SubscriptionPlanNotFoundError,
)
from app.modules.abonnement.domain.depots import (
    AbstractSubscriptionPlanRepository,
    AbstractSubscriptionRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams


# ── Plans d'abonnement ────────────────────────────────────────────────────────

class ListPlansUseCase:
    def __init__(self, repo: AbstractSubscriptionPlanRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[SubscriptionPlan]:
        return await self._repo.list_active()


class GetPlanBySlugUseCase:
    def __init__(self, repo: AbstractSubscriptionPlanRepository) -> None:
        self._repo = repo

    async def execute(self, identifiant_url: str) -> SubscriptionPlan:
        forfait = await self._repo.get_by_slug(identifiant_url)
        if forfait is None:
            raise SubscriptionPlanNotFoundError(identifiant_url)
        return forfait


class CreatePlanUseCase:
    def __init__(self, repo: AbstractSubscriptionPlanRepository) -> None:
        self._repo = repo

    async def execute(
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
        return await self._repo.create(
            nom=nom, identifiant_url=identifiant_url, prix=prix, periode_facturation=periode_facturation,
            description=description, jours_essai=jours_essai,
            est_mis_en_avant=est_mis_en_avant, ordre_affichage=ordre_affichage,
        )


class UpdatePlanUseCase:
    def __init__(self, repo: AbstractSubscriptionPlanRepository) -> None:
        self._repo = repo

    async def execute(self, id_plan: int, **kwargs: Any) -> SubscriptionPlan:
        mis_a_jour = await self._repo.update(id_plan, **kwargs)
        if mis_a_jour is None:
            raise SubscriptionPlanNotFoundError(id_plan)
        return mis_a_jour


class UpsertPlanLimitationUseCase:
    def __init__(self, repo: AbstractSubscriptionPlanRepository) -> None:
        self._repo = repo

    async def execute(self, id_plan: int, fonctionnalite: str, valeur: str):
        plan = await self._repo.get_by_id(id_plan)
        if plan is None:
            raise SubscriptionPlanNotFoundError(id_plan)
        return await self._repo.upsert_limitation(id_plan, fonctionnalite, valeur)


class DeletePlanLimitationUseCase:
    def __init__(self, repo: AbstractSubscriptionPlanRepository) -> None:
        self._repo = repo

    async def execute(self, id_plan: int, fonctionnalite: str) -> None:
        supprime = await self._repo.delete_limitation(id_plan, fonctionnalite)
        if not supprime:
            raise PlanLimitationNotFoundError(id_plan, fonctionnalite)


# ── Abonnements ───────────────────────────────────────────────────────────────

class SubscribeUseCase:
    """
    Règles métier :
    1. Vérifier que la clinique n'a pas déjà un abonnement actif ou en essai
    2. Si jours_essai > 0 → statut='trial', fin = maintenant + jours_essai jours
    3. Sinon → statut='active', fin calculée selon periode_facturation (30j ou 365j)
    """
    def __init__(
        self,
        plan_repo: AbstractSubscriptionPlanRepository,
        sub_repo: AbstractSubscriptionRepository,
    ) -> None:
        self._plan_repo = plan_repo
        self._sub_repo = sub_repo

    async def execute(self, id_clinique: int, id_plan: int) -> Subscription:
        # 1. Vérifier qu'il n'existe pas d'abonnement actif
        existant = await self._sub_repo.get_active_for_clinic(id_clinique)
        if existant is not None:
            raise ActiveSubscriptionExistsError(id_clinique)

        # 2. Charger le plan d'abonnement
        forfait = await self._plan_repo.get_by_id(id_plan)
        if forfait is None:
            raise SubscriptionPlanNotFoundError(id_plan)

        maintenant = datetime.now(timezone.utc).replace(tzinfo=None)

        if forfait.jours_essai > 0:
            statut = "trial"
            fin = maintenant + timedelta(days=forfait.jours_essai)
        else:
            statut = "active"
            fin = maintenant + timedelta(days=forfait.period_days())

        return await self._sub_repo.create(
            id_clinique=id_clinique,
            id_plan=id_plan,
            statut=statut,
            debut_le=maintenant,
            fin_le=fin,
        )


class GetCurrentSubscriptionUseCase:
    def __init__(self, repo: AbstractSubscriptionRepository) -> None:
        self._repo = repo

    async def execute(self, id_clinique: int) -> Subscription:
        abonnement = await self._repo.get_active_for_clinic(id_clinique)
        if abonnement is None:
            raise SubscriptionNotFoundError(0)
        return abonnement


class CancelSubscriptionUseCase:
    def __init__(self, repo: AbstractSubscriptionRepository) -> None:
        self._repo = repo

    async def execute(self, subscription_id: int) -> Subscription:
        abonnement = await self._repo.get_by_id(subscription_id)
        if abonnement is None:
            raise SubscriptionNotFoundError(subscription_id)
        maintenant = datetime.now(timezone.utc).replace(tzinfo=None)
        abonnement.cancel(maintenant)
        mis_a_jour = await self._repo.update(
            subscription_id,
            renouvellement_auto=False,
            statut="cancelled",
            annule_le=maintenant,
        )
        if mis_a_jour is None:
            raise SubscriptionNotFoundError(subscription_id)
        return mis_a_jour


class RenewSubscriptionUseCase:
    """
    Règles métier :
    1. Vérifier que l'abonnement est actif ou expiré (pas annulé)
    2. Calculer la nouvelle fin = max(maintenant, ancienne fin) + période
    3. statut = 'active', renouvellement_auto = true
    """
    def __init__(
        self,
        plan_repo: AbstractSubscriptionPlanRepository,
        sub_repo: AbstractSubscriptionRepository,
    ) -> None:
        self._plan_repo = plan_repo
        self._sub_repo = sub_repo

    async def execute(
        self,
        subscription_id: int,
        id_plan: Optional[int] = None,
    ) -> Subscription:
        abonnement = await self._sub_repo.get_by_id(subscription_id)
        if abonnement is None:
            raise SubscriptionNotFoundError(subscription_id)

        if abonnement.statut == "cancelled":
            raise CannotRenewCancelledError(subscription_id)

        # Changement de plan optionnel
        id_forfait_cible = id_plan if id_plan is not None else abonnement.id_plan
        forfait = await self._plan_repo.get_by_id(id_forfait_cible)
        if forfait is None:
            raise SubscriptionPlanNotFoundError(id_forfait_cible)

        maintenant = datetime.now(timezone.utc).replace(tzinfo=None)
        nouvelle_fin = max(maintenant, abonnement.fin_le) + timedelta(days=forfait.period_days())

        mis_a_jour = await self._sub_repo.update(
            subscription_id,
            id_plan=id_forfait_cible,
            statut="active",
            fin_le=nouvelle_fin,
            renouvellement_auto=True,
        )
        if mis_a_jour is None:
            raise SubscriptionNotFoundError(subscription_id)
        return mis_a_jour


class ListAdminSubscriptionsUseCase:
    def __init__(self, repo: AbstractSubscriptionRepository) -> None:
        self._repo = repo

    async def execute(self, params: PaginationParams) -> Page[Subscription]:
        data, total = await self._repo.list_paginated(params)
        return Page.create(data, total, params)


class GetAdminSubscriptionUseCase:
    def __init__(self, repo: AbstractSubscriptionRepository) -> None:
        self._repo = repo

    async def execute(self, subscription_id: int) -> Subscription:
        abonnement = await self._repo.get_by_id(subscription_id)
        if abonnement is None:
            raise SubscriptionNotFoundError(subscription_id)
        return abonnement


class ForceSubscriptionStatusUseCase:
    def __init__(self, repo: AbstractSubscriptionRepository) -> None:
        self._repo = repo

    async def execute(self, subscription_id: int, new_status: str) -> Subscription:
        mis_a_jour = await self._repo.update(subscription_id, statut=new_status)
        if mis_a_jour is None:
            raise SubscriptionNotFoundError(subscription_id)
        return mis_a_jour
