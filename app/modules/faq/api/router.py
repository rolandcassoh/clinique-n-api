"""Router FastAPI du module FAQ."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.faq.api.schemas import FAQCreateRequest, FAQSchema, FAQUpdateRequest
from app.modules.faq.application.use_cases import (
    CreateFAQUseCase,
    DeleteFAQUseCase,
    GetFAQUseCase,
    ListActiveFAQsUseCase,
    UpdateFAQUseCase,
)
from app.modules.faq.domain.exceptions import FAQNotFoundError
from app.modules.faq.infrastructure.repositories import SQLAlchemyFAQRepository
from app.shared.exceptions.domain import EntityNotFoundError
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["FAQ"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
AdminDep = Annotated[dict[str, Any], Depends(require_role("admin", "super-admin"))]


def _repo(db: DbDep) -> SQLAlchemyFAQRepository:
    return SQLAlchemyFAQRepository(db)


# ---------------------------------------------------------------------------
# Endpoints publics
# ---------------------------------------------------------------------------


@router.get("/faq", response_model=Page[FAQSchema])
async def list_faqs(
    category: Annotated[str | None, Query(description="Filtre par catégorie")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyFAQRepository = Depends(_repo),
) -> Page[FAQSchema]:
    """Liste des FAQs actives (publique). Filtre optionnel par catégorie."""
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListActiveFAQsUseCase(repo)
    result = await uc.execute(params, category)
    return result  # type: ignore[return-value]


@router.get("/faq/{faq_id}", response_model=FAQSchema)
async def get_faq(
    faq_id: int,
    repo: SQLAlchemyFAQRepository = Depends(_repo),
) -> FAQSchema:
    """Détail d'une FAQ (publique)."""
    uc = GetFAQUseCase(repo)
    try:
        faq = await uc.execute(faq_id)
    except (FAQNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FAQSchema.model_validate(faq)


# ---------------------------------------------------------------------------
# Endpoints admin (protégés)
# ---------------------------------------------------------------------------


@router.post(
    "/admin/faq",
    response_model=FAQSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def create_faq(
    payload: FAQCreateRequest,
    repo: SQLAlchemyFAQRepository = Depends(_repo),
) -> FAQSchema:
    """Créer une FAQ (admin)."""
    uc = CreateFAQUseCase(repo)
    faq = await uc.execute(
        question=payload.question,
        answer=payload.answer,
        category=payload.category,
        is_active=payload.is_active,
        sort_order=payload.sort_order,
    )
    return FAQSchema.model_validate(faq)


@router.put(
    "/admin/faq/{faq_id}",
    response_model=FAQSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def update_faq(
    faq_id: int,
    payload: FAQUpdateRequest,
    repo: SQLAlchemyFAQRepository = Depends(_repo),
) -> FAQSchema:
    """Modifier une FAQ (admin)."""
    uc = UpdateFAQUseCase(repo)
    try:
        faq = await uc.execute(
            faq_id=faq_id,
            question=payload.question,
            answer=payload.answer,
            category=payload.category,
            is_active=payload.is_active,
            sort_order=payload.sort_order,
        )
    except (FAQNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FAQSchema.model_validate(faq)


@router.delete(
    "/admin/faq/{faq_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def delete_faq(
    faq_id: int,
    repo: SQLAlchemyFAQRepository = Depends(_repo),
) -> None:
    """Supprimer (soft delete) une FAQ (admin)."""
    uc = DeleteFAQUseCase(repo)
    try:
        await uc.execute(faq_id)
    except (FAQNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
