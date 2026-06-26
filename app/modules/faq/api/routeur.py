"""Routeur FastAPI du module FAQ — gestion des questions fréquentes."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.faq.api.schemas import FAQCreateRequest, FAQSchema, FAQUpdateRequest
from app.modules.faq.application.cas_utilisation import (
    CreateFAQUseCase,
    DeleteFAQUseCase,
    GetFAQUseCase,
    ListActiveFAQsUseCase,
    UpdateFAQUseCase,
)
from app.modules.faq.domain.exceptions import FAQNotFoundError
from app.modules.faq.infrastructure.depots import SQLAlchemyFAQRepository
from app.shared.exceptions.domain import EntityNotFoundError
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["FAQ - Questions Fréquentes"])

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
    resultat = await uc.execute(params, category)
    return resultat  # type: ignore[return-valeur]


@router.get("/faq/{faq_id}", response_model=FAQSchema)
async def get_faq(
    faq_id: int,
    repo: SQLAlchemyFAQRepository = Depends(_repo),
) -> FAQSchema:
    """Détail d'une FAQ (publique)."""
    uc = GetFAQUseCase(repo)
    try:
        element = await uc.execute(faq_id)
    except (FAQNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FAQSchema.model_validate(element)


# ---------------------------------------------------------------------------
# Endpoints admin (protégés)
# ---------------------------------------------------------------------------


@router.post(
    "/admin/faq",
    response_model=FAQSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def create_faq(
    payload: FAQCreateRequest,
    repo: SQLAlchemyFAQRepository = Depends(_repo),
) -> FAQSchema:
    """Créer une FAQ (admin)."""
    uc = CreateFAQUseCase(repo)
    element = await uc.execute(
        question=payload.question,
        reponse=payload.reponse,
        category=payload.category,
        est_actif=payload.est_actif,
        ordre_affichage=payload.ordre_affichage,
    )
    return FAQSchema.model_validate(element)


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
        element = await uc.execute(
            faq_id=faq_id,
            question=payload.question,
            reponse=payload.reponse,
            category=payload.category,
            est_actif=payload.est_actif,
            ordre_affichage=payload.ordre_affichage,
        )
    except (FAQNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FAQSchema.model_validate(element)


@router.delete(
    "/admin/faq/{faq_id}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
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
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
