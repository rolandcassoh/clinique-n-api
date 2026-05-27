from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.promotion.api.schemas import (
    PromotionCreateSchema,
    PromotionSchema,
    PromotionUpdateSchema,
    PromotionUseSchema,
    ValidatePromotionRequestSchema,
    ValidatePromotionResponseSchema,
)
from app.modules.promotion.application.use_cases import (
    CreatePromotionUseCase,
    DeletePromotionUseCase,
    GetPromotionUseCase,
    ListPromotionUsesUseCase,
    ListPromotionsUseCase,
    UpdatePromotionUseCase,
    ValidatePromotionUseCase,
)
from app.modules.promotion.domain.exceptions import (
    PromotionCodeConflictError,
    PromotionNotFoundError,
)
from app.modules.promotion.infrastructure.repositories import SQLPromotionRepository
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["promotions"])


def _repo(db: AsyncSession = Depends(get_db)) -> SQLPromotionRepository:
    return SQLPromotionRepository(db)


# ── Public ──────────────────────────────────────────────────────────────────


@router.post(
    "/promotions/validate",
    response_model=ValidatePromotionResponseSchema,
)
async def validate_promotion(
    body: ValidatePromotionRequestSchema,
    _: dict[str, Any] = Depends(get_current_user),
    repo: SQLPromotionRepository = Depends(_repo),
) -> ValidatePromotionResponseSchema:
    result = await ValidatePromotionUseCase(repo).execute(
        code=body.code,
        amount=body.amount,
        applicable_to=body.applicable_to,
    )
    promo_schema = (
        PromotionSchema.model_validate(result.promotion.__dict__)
        if result.promotion
        else None
    )
    return ValidatePromotionResponseSchema(
        valid=result.valid,
        discount_amount=float(result.discount_amount),
        promotion=promo_schema,
        reason=result.reason,
    )


# ── Admin ────────────────────────────────────────────────────────────────────


@router.get(
    "/admin/promotions",
    response_model=Page[PromotionSchema],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def list_promotions(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    repo: SQLPromotionRepository = Depends(_repo),
) -> Page[PromotionSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    page_result = await ListPromotionsUseCase(repo).execute(params)
    return Page[PromotionSchema](
        data=[PromotionSchema.model_validate(p.__dict__) for p in page_result.data],
        total=page_result.total,
        page=page_result.page,
        per_page=page_result.per_page,
        total_pages=page_result.total_pages,
    )


@router.get(
    "/admin/promotions/{promotion_id}",
    response_model=PromotionSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def get_promotion(
    promotion_id: int,
    repo: SQLPromotionRepository = Depends(_repo),
) -> PromotionSchema:
    try:
        promo = await GetPromotionUseCase(repo).execute(promotion_id)
    except PromotionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return PromotionSchema.model_validate(promo.__dict__)


@router.post(
    "/admin/promotions",
    response_model=PromotionSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def create_promotion(
    body: PromotionCreateSchema,
    repo: SQLPromotionRepository = Depends(_repo),
) -> PromotionSchema:
    try:
        promo = await CreatePromotionUseCase(repo).execute(
            code=body.code,
            name=body.name,
            type=body.type,
            value=body.value,
            min_order_amount=body.min_order_amount,
            max_discount_amount=body.max_discount_amount,
            usage_limit=body.usage_limit,
            starts_at=body.starts_at,
            expires_at=body.expires_at,
            is_active=body.is_active,
            applicable_to=body.applicable_to,
        )
    except PromotionCodeConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return PromotionSchema.model_validate(promo.__dict__)


@router.put(
    "/admin/promotions/{promotion_id}",
    response_model=PromotionSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def update_promotion(
    promotion_id: int,
    body: PromotionUpdateSchema,
    repo: SQLPromotionRepository = Depends(_repo),
) -> PromotionSchema:
    try:
        promo = await UpdatePromotionUseCase(repo).execute(
            promotion_id=promotion_id,
            code=body.code,
            name=body.name,
            type=body.type,
            value=body.value,
            min_order_amount=body.min_order_amount,
            max_discount_amount=body.max_discount_amount,
            usage_limit=body.usage_limit,
            starts_at=body.starts_at,
            expires_at=body.expires_at,
            is_active=body.is_active,
            applicable_to=body.applicable_to,
        )
    except PromotionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except PromotionCodeConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return PromotionSchema.model_validate(promo.__dict__)


@router.delete(
    "/admin/promotions/{promotion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def delete_promotion(
    promotion_id: int,
    repo: SQLPromotionRepository = Depends(_repo),
) -> None:
    try:
        await DeletePromotionUseCase(repo).execute(promotion_id)
    except PromotionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


@router.get(
    "/admin/promotions/{promotion_id}/uses",
    response_model=Page[PromotionUseSchema],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def list_promotion_uses(
    promotion_id: int,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    repo: SQLPromotionRepository = Depends(_repo),
) -> Page[PromotionUseSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    try:
        page_result = await ListPromotionUsesUseCase(repo).execute(promotion_id, params)
    except PromotionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return Page[PromotionUseSchema](
        data=[PromotionUseSchema.model_validate(u.__dict__) for u in page_result.data],
        total=page_result.total,
        page=page_result.page,
        per_page=page_result.per_page,
        total_pages=page_result.total_pages,
    )
