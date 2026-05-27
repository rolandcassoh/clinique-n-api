"""API router — module subscription."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.subscription.api.schemas import (
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
from app.modules.subscription.application.use_cases import (
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
from app.modules.subscription.domain.exceptions import (
    ActiveSubscriptionExistsError,
    CannotRenewCancelledError,
    PlanLimitationNotFoundError,
    SubscriptionNotFoundError,
    SubscriptionPlanNotFoundError,
)
from app.modules.subscription.infrastructure.repositories import (
    SQLSubscriptionPlanRepository,
    SQLSubscriptionRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Subscriptions"])

_admin_dep = require_role("admin", "super-admin")


def _plan_repo(db: AsyncSession = Depends(get_db)) -> SQLSubscriptionPlanRepository:
    return SQLSubscriptionPlanRepository(db)


def _sub_repo(db: AsyncSession = Depends(get_db)) -> SQLSubscriptionRepository:
    return SQLSubscriptionRepository(db)


def _plan_schema(plan) -> SubscriptionPlanSchema:
    data = plan.__dict__.copy()
    data["limitations"] = [PlanLimitationSchema.model_validate(l.__dict__) for l in plan.limitations]
    return SubscriptionPlanSchema.model_validate(data)


# ── Public — Plans ────────────────────────────────────────────────────────────

@router.get("/subscription-plans", response_model=list[SubscriptionPlanSchema])
async def list_plans(
    repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
) -> list[SubscriptionPlanSchema]:
    plans = await ListPlansUseCase(repo).execute()
    return [_plan_schema(p) for p in plans]


@router.get("/subscription-plans/{slug}", response_model=SubscriptionPlanSchema)
async def get_plan(
    slug: str,
    repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
) -> SubscriptionPlanSchema:
    try:
        plan = await GetPlanBySlugUseCase(repo).execute(slug)
    except SubscriptionPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return _plan_schema(plan)


# ── Authentifié — Souscriptions ───────────────────────────────────────────────

@router.post(
    "/subscriptions",
    response_model=SubscriptionSchema,
    status_code=status.HTTP_201_CREATED,
)
async def subscribe(
    body: SubscribeSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    plan_repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
    sub_repo: SQLSubscriptionRepository = Depends(_sub_repo),
) -> SubscriptionSchema:
    try:
        sub = await SubscribeUseCase(plan_repo, sub_repo).execute(
            clinic_id=body.clinic_id, plan_id=body.plan_id
        )
    except ActiveSubscriptionExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    except SubscriptionPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return SubscriptionSchema.model_validate(sub.__dict__)


@router.get("/subscriptions/current", response_model=SubscriptionSchema)
async def get_current_subscription(
    clinic_id: int = Query(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLSubscriptionRepository = Depends(_sub_repo),
) -> SubscriptionSchema:
    try:
        sub = await GetCurrentSubscriptionUseCase(repo).execute(clinic_id)
    except SubscriptionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return SubscriptionSchema.model_validate(sub.__dict__)


@router.post("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionSchema)
async def cancel_subscription(
    subscription_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLSubscriptionRepository = Depends(_sub_repo),
) -> SubscriptionSchema:
    try:
        sub = await CancelSubscriptionUseCase(repo).execute(subscription_id)
    except SubscriptionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return SubscriptionSchema.model_validate(sub.__dict__)


@router.post("/subscriptions/{subscription_id}/renew", response_model=SubscriptionSchema)
async def renew_subscription(
    subscription_id: int,
    body: RenewSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    plan_repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
    sub_repo: SQLSubscriptionRepository = Depends(_sub_repo),
) -> SubscriptionSchema:
    try:
        sub = await RenewSubscriptionUseCase(plan_repo, sub_repo).execute(
            subscription_id, plan_id=body.plan_id
        )
    except SubscriptionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except CannotRenewCancelledError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    except SubscriptionPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return SubscriptionSchema.model_validate(sub.__dict__)


# ── Admin — Subscriptions ─────────────────────────────────────────────────────

@router.get(
    "/admin/subscriptions",
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
    "/admin/subscriptions/{subscription_id}",
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return SubscriptionSchema.model_validate(sub.__dict__)


@router.patch(
    "/admin/subscriptions/{subscription_id}/status",
    response_model=SubscriptionSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_force_status(
    subscription_id: int,
    body: ForceStatusSchema,
    repo: SQLSubscriptionRepository = Depends(_sub_repo),
) -> SubscriptionSchema:
    try:
        sub = await ForceSubscriptionStatusUseCase(repo).execute(subscription_id, body.status)
    except SubscriptionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return SubscriptionSchema.model_validate(sub.__dict__)


# ── Admin — Plans ─────────────────────────────────────────────────────────────

@router.post(
    "/admin/subscription-plans",
    response_model=SubscriptionPlanSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_plan(
    body: SubscriptionPlanCreateSchema,
    repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
) -> SubscriptionPlanSchema:
    plan = await CreatePlanUseCase(repo).execute(
        name=body.name, slug=body.slug, price=body.price,
        billing_period=body.billing_period, description=body.description,
        trial_days=body.trial_days, is_featured=body.is_featured, sort_order=body.sort_order,
    )
    return _plan_schema(plan)


@router.put(
    "/admin/subscription-plans/{plan_id}",
    response_model=SubscriptionPlanSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_update_plan(
    plan_id: int,
    body: SubscriptionPlanUpdateSchema,
    repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
) -> SubscriptionPlanSchema:
    try:
        plan = await UpdatePlanUseCase(repo).execute(
            plan_id,
            **{k: v for k, v in body.model_dump(exclude_none=True).items()},
        )
    except SubscriptionPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return _plan_schema(plan)


@router.post(
    "/admin/subscription-plans/{plan_id}/limitations",
    response_model=PlanLimitationSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(_admin_dep)],
)
async def admin_upsert_limitation(
    plan_id: int,
    body: PlanLimitationUpsertSchema,
    repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
) -> PlanLimitationSchema:
    try:
        limitation = await UpsertPlanLimitationUseCase(repo).execute(
            plan_id, body.feature, body.value
        )
    except SubscriptionPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return PlanLimitationSchema.model_validate(limitation.__dict__)


@router.delete(
    "/admin/subscription-plans/{plan_id}/limitations/{feature}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_limitation(
    plan_id: int,
    feature: str,
    repo: SQLSubscriptionPlanRepository = Depends(_plan_repo),
) -> None:
    try:
        await DeletePlanLimitationUseCase(repo).execute(plan_id, feature)
    except PlanLimitationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
