"""Routeur API — module abonnements."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.abonnement.api.schemas import (
    ForceStatusSchema,
    PlanLimitationSchema,
    PlanLimitationUpsertSchema,
    RenewSchema,
    SubscribeSchema,
    SubscriptionPlanCreateSchema,
    SubscriptionPlanSchema,
    SubscriptionPlanUpdateSchema,
    SubscriptionSchema,
)
from app.modules.abonnement.application.cas_utilisation import (
    CancelSubscriptionUseCase,
    CreatePlanUseCase,
    DeletePlanLimitationUseCase,
    ForceSubscriptionStatusUseCase,
    GetAdminSubscriptionUseCase,
    GetCurrentSubscriptionUseCase,
    GetPlanBySlugUseCase,
    ListAdminSubscriptionsUseCase,
    ListPlansUseCase,
    RenewSubscriptionUseCase,
    SubscribeUseCase,
    UpdatePlanUseCase,
    UpsertPlanLimitationUseCase,
)
from app.modules.abonnement.domain.exceptions import (
    ActiveSubscriptionExistsError,
    CannotRenewCancelledError,
    PlanLimitationNotFoundError,
    SubscriptionNotFoundError,
    SubscriptionPlanNotFoundError,
)
from app.modules.abonnement.infrastructure.depots import (
    SQLSubscriptionPlanRepository,
    SQLSubscriptionRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Abonnements"])

_admin_dep = require_role("admin", "super-admin")


def _plan_repo(db: AsyncSession = Depends(get_db)) -> SQLSubscriptionPlanRepository:
    return SQLSubscriptionPlanRepository(db)


def _sub_repo(db: AsyncSession = Depends(get_db)) -> SQLSubscriptionRepository:
    return SQLSubscriptionRepository(db)


def _plan_schema(plan) -> SubscriptionPlanSchema:
    data = plan.__dict__.copy()
    data["limitations"] = [PlanLimitationSchema.model_validate(l.__dict__) for l in plan.limitations]
    return SubscriptionPlanSchema.model_validate(data)


# ── Accès public — Plans d'abonnement ────────────────────────────────────────

@router.get("/plans-abonnement", response_model=list[SubscriptionPlanSchema])
async def list_plans(
    repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
) -> list[SubscriptionPlanSchema]:
    plans = await ListPlansUseCase(repo).execute()
    return [_plan_schema(p) for p in plans]


@router.get("/plans-abonnement/{identifiant_url}", response_model=SubscriptionPlanSchema)
async def get_plan(
    identifiant_url: str,
    repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
) -> SubscriptionPlanSchema:
    try:
        plan = await GetPlanBySlugUseCase(repo).execute(identifiant_url)
    except SubscriptionPlanNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return _plan_schema(plan)


# ── Authentifié — Gestion des abonnements ────────────────────────────────────

@router.post(
    "/abonnements",
    response_model=SubscriptionSchema,
    status_code=statut.HTTP_201_CREATED,
)
async def subscribe(
    body: SubscribeSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    plan_repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
    sub_repo: SQLSubscriptionRepository = Depends(_sub_repo),
) -> SubscriptionSchema:
    try:
        sub = await SubscribeUseCase(plan_repo, sub_repo).execute(
            id_clinique=body.id_clinique, id_plan=body.id_plan
        )
    except ActiveSubscriptionExistsError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=exc.message)
    except SubscriptionPlanNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return SubscriptionSchema.model_validate(sub.__dict__)


@router.get("/abonnements/actuel", response_model=SubscriptionSchema)
async def get_current_subscription(
    id_clinique: int = Query(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLSubscriptionRepository = Depends(_sub_repo),
) -> SubscriptionSchema:
    try:
        sub = await GetCurrentSubscriptionUseCase(repo).execute(id_clinique)
    except SubscriptionNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return SubscriptionSchema.model_validate(sub.__dict__)


@router.post("/abonnements/{subscription_id}/annuler", response_model=SubscriptionSchema)
async def cancel_subscription(
    subscription_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLSubscriptionRepository = Depends(_sub_repo),
) -> SubscriptionSchema:
    try:
        sub = await CancelSubscriptionUseCase(repo).execute(subscription_id)
    except SubscriptionNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return SubscriptionSchema.model_validate(sub.__dict__)


@router.post("/abonnements/{subscription_id}/renouveler", response_model=SubscriptionSchema)
async def renew_subscription(
    subscription_id: int,
    body: RenewSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    plan_repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
    sub_repo: SQLSubscriptionRepository = Depends(_sub_repo),
) -> SubscriptionSchema:
    try:
        sub = await RenewSubscriptionUseCase(plan_repo, sub_repo).execute(
            subscription_id, id_plan=body.id_plan
        )
    except SubscriptionNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    except CannotRenewCancelledError as exc:
        raise HTTPException(status_code=statut.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    except SubscriptionPlanNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return SubscriptionSchema.model_validate(sub.__dict__)


# ── Admin — Administration des abonnements ───────────────────────────────────

@router.get(
    "/admin/abonnements",
    response_model=Page[SubscriptionSchema],
    dependencies=[Depends(_admin_dep)],
)
async def admin_list_subscriptions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    repo: SQLSubscriptionRepository = Depends(_sub_repo),
) -> Page[SubscriptionSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    page_result = await ListAdminSubscriptionsUseCase(repo).execute(params)
    return Page[SubscriptionSchema](
        data=[SubscriptionSchema.model_validate(s.__dict__) for s in page_result.data],
        total=page_result.total,
        page=page_result.page,
        per_page=page_result.per_page,
        total_pages=page_result.total_pages,
    )


@router.get(
    "/admin/abonnements/{subscription_id}",
    response_model=SubscriptionSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_get_subscription(
    subscription_id: int,
    repo: SQLSubscriptionRepository = Depends(_sub_repo),
) -> SubscriptionSchema:
    try:
        sub = await GetAdminSubscriptionUseCase(repo).execute(subscription_id)
    except SubscriptionNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return SubscriptionSchema.model_validate(sub.__dict__)


@router.patch(
    "/admin/abonnements/{subscription_id}/statut",
    response_model=SubscriptionSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_force_status(
    subscription_id: int,
    body: ForceStatusSchema,
    repo: SQLSubscriptionRepository = Depends(_sub_repo),
) -> SubscriptionSchema:
    try:
        sub = await ForceSubscriptionStatusUseCase(repo).execute(subscription_id, body.statut)
    except SubscriptionNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return SubscriptionSchema.model_validate(sub.__dict__)


# ── Admin — Gestion des plans d'abonnement ───────────────────────────────────

@router.post(
    "/admin/plans-abonnement",
    response_model=SubscriptionPlanSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_plan(
    body: SubscriptionPlanCreateSchema,
    repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
) -> SubscriptionPlanSchema:
    plan = await CreatePlanUseCase(repo).execute(
        nom=body.nom, identifiant_url=body.identifiant_url, prix=body.prix,
        periode_facturation=body.periode_facturation, description=body.description,
        jours_essai=body.jours_essai, est_mis_en_avant=body.est_mis_en_avant, ordre_affichage=body.ordre_affichage,
    )
    return _plan_schema(plan)


@router.put(
    "/admin/plans-abonnement/{id_plan}",
    response_model=SubscriptionPlanSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_update_plan(
    id_plan: int,
    body: SubscriptionPlanUpdateSchema,
    repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
) -> SubscriptionPlanSchema:
    try:
        plan = await UpdatePlanUseCase(repo).execute(
            id_plan,
            **{k: v for k, v in body.model_dump(exclude_none=True).items()},
        )
    except SubscriptionPlanNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return _plan_schema(plan)


@router.post(
    "/admin/plans-abonnement/{id_plan}/limitations",
    response_model=PlanLimitationSchema,
    status_code=statut.HTTP_200_OK,
    dependencies=[Depends(_admin_dep)],
)
async def admin_upsert_limitation(
    id_plan: int,
    body: PlanLimitationUpsertSchema,
    repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
) -> PlanLimitationSchema:
    try:
        limitation = await UpsertPlanLimitationUseCase(repo).execute(
            id_plan, body.fonctionnalite, body.valeur
        )
    except SubscriptionPlanNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return PlanLimitationSchema.model_validate(limitation.__dict__)


@router.delete(
    "/admin/plans-abonnement/{id_plan}/limitations/{fonctionnalite}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_limitation(
    id_plan: int,
    fonctionnalite: str,
    repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
) -> None:
    try:
        await DeletePlanLimitationUseCase(repo).execute(id_plan, fonctionnalite)
    except PlanLimitationNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
