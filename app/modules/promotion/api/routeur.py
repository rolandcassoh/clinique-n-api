"""Routeur FastAPI du module promotion — codes promo et validation."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status as statut
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
from app.modules.promotion.application.cas_utilisation import (
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
from app.modules.promotion.infrastructure.depots import SQLPromotionRepository
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["promotions"])


def _repo(db: AsyncSession = Depends(get_db)) -> SQLPromotionRepository:
    return SQLPromotionRepository(db)


# ── Public ──────────────────────────────────────────────────────────────────


@router.post(
    "/promotions/valider",
    response_model=ValidatePromotionResponseSchema,
)
async def validate_promotion(
    body: ValidatePromotionRequestSchema,
    _: dict[str, Any] = Depends(get_current_user),
    repo: SQLPromotionRepository = Depends(_repo),
) -> ValidatePromotionResponseSchema:
    """Valider un code promo (utilisateur connecté)."""
    resultat_validation = await ValidatePromotionUseCase(repo).execute(
        code=body.code,
        montant=body.montant,
        applicable_a=body.applicable_a,
    )
    promo_schema = (
        PromotionSchema.model_validate(resultat_validation.promotion.__dict__)
        if resultat_validation.promotion
        else None
    )
    return ValidatePromotionResponseSchema(
        valid=resultat_validation.valid,
        montant_remise=float(resultat_validation.montant_remise),
        promotion=promo_schema,
        motif=resultat_validation.motif,
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
    """Liste toutes les promotions (admin)."""
    params = PaginationParams(page=page, per_page=per_page)
    page_resultat = await ListPromotionsUseCase(repo).execute(params)
    return Page[PromotionSchema](
        data=[PromotionSchema.model_validate(p.__dict__) for p in page_resultat.data],
        total=page_resultat.total,
        page=page_resultat.page,
        per_page=page_resultat.per_page,
        total_pages=page_resultat.total_pages,
    )


@router.get(
    "/admin/promotions/{id_promotion}",
    response_model=PromotionSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def get_promotion(
    id_promotion: int,
    repo: SQLPromotionRepository = Depends(_repo),
) -> PromotionSchema:
    """Détail d'une promotion (admin)."""
    try:
        promotion_obj = await GetPromotionUseCase(repo).execute(id_promotion)
    except PromotionNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return PromotionSchema.model_validate(promotion_obj.__dict__)


@router.post(
    "/admin/promotions",
    response_model=PromotionSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def create_promotion(
    body: PromotionCreateSchema,
    repo: SQLPromotionRepository = Depends(_repo),
) -> PromotionSchema:
    """Créer une promotion (admin)."""
    try:
        promotion_obj = await CreatePromotionUseCase(repo).execute(
            code=body.code,
            nom=body.nom,
            type=body.type,
            valeur=body.valeur,
            montant_min_commande=body.montant_min_commande,
            remise_maximale=body.remise_maximale,
            limite_utilisation=body.limite_utilisation,
            debut_le=body.debut_le,
            expire_le=body.expire_le,
            est_actif=body.est_actif,
            applicable_a=body.applicable_a,
        )
    except PromotionCodeConflictError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=exc.message)
    return PromotionSchema.model_validate(promotion_obj.__dict__)


@router.put(
    "/admin/promotions/{id_promotion}",
    response_model=PromotionSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def update_promotion(
    id_promotion: int,
    body: PromotionUpdateSchema,
    repo: SQLPromotionRepository = Depends(_repo),
) -> PromotionSchema:
    """Modifier une promotion (admin)."""
    try:
        promotion_obj = await UpdatePromotionUseCase(repo).execute(
            id_promotion=id_promotion,
            code=body.code,
            nom=body.nom,
            type=body.type,
            valeur=body.valeur,
            montant_min_commande=body.montant_min_commande,
            remise_maximale=body.remise_maximale,
            limite_utilisation=body.limite_utilisation,
            debut_le=body.debut_le,
            expire_le=body.expire_le,
            est_actif=body.est_actif,
            applicable_a=body.applicable_a,
        )
    except PromotionNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    except PromotionCodeConflictError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=exc.message)
    return PromotionSchema.model_validate(promotion_obj.__dict__)


@router.delete(
    "/admin/promotions/{id_promotion}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def delete_promotion(
    id_promotion: int,
    repo: SQLPromotionRepository = Depends(_repo),
) -> None:
    try:
        await DeletePromotionUseCase(repo).execute(id_promotion)
    except PromotionNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)


@router.get(
    "/admin/promotions/{id_promotion}/utilisations",
    response_model=Page[PromotionUseSchema],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def list_promotion_uses(
    id_promotion: int,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    repo: SQLPromotionRepository = Depends(_repo),
) -> Page[PromotionUseSchema]:
    """Liste les utilisations d'une promotion (admin)."""
    params = PaginationParams(page=page, per_page=per_page)
    try:
        page_resultat = await ListPromotionUsesUseCase(repo).execute(id_promotion, params)
    except PromotionNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return Page[PromotionUseSchema](
        data=[PromotionUseSchema.model_validate(u.__dict__) for u in page_resultat.data],
        total=page_resultat.total,
        page=page_resultat.page,
        per_page=page_resultat.per_page,
        total_pages=page_resultat.total_pages,
    )
