"""Routeur FastAPI du module page (CMS) — pages statiques."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.page.api.schemas import (
    PageCreateRequest,
    PageDetailSchema,
    PageSchema,
    PageUpdateRequest,
)
from app.modules.page.application.cas_utilisation import (
    CreatePageUseCase,
    GetPageBySlugUseCase,
    ListPagesUseCase,
    UpdatePageUseCase,
)
from app.modules.page.domain.exceptions import PageNotFoundError, PageSlugAlreadyExistsError
from app.modules.page.infrastructure.depots import SQLAlchemyPageRepository
from app.shared.exceptions.domain import EntityNotFoundError

router = APIRouter(tags=["Pages"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _repo(db: DbDep) -> SQLAlchemyPageRepository:
    return SQLAlchemyPageRepository(db)


# ---------------------------------------------------------------------------
# Endpoints publics
# ---------------------------------------------------------------------------


@router.get("/pages", response_model=list[PageSchema])
async def list_pages(
    repo: SQLAlchemyPageRepository = Depends(_repo),
) -> list[PageSchema]:
    """Liste toutes les pages publiées (sans contenu)."""
    uc = ListPagesUseCase(repo)
    elements = await uc.execute()
    return [PageSchema.model_validate(p) for p in elements]


@router.get("/pages/{identifiant_url}", response_model=PageDetailSchema)
async def get_page(
    identifiant_url: str,
    repo: SQLAlchemyPageRepository = Depends(_repo),
) -> PageDetailSchema:
    """Détail d'une page publiée par identifiant_url (avec contenu complet)."""
    uc = GetPageBySlugUseCase(repo)
    try:
        element = await uc.execute(identifiant_url)
    except (PageNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PageDetailSchema.model_validate(element)


# ---------------------------------------------------------------------------
# Endpoints admin
# ---------------------------------------------------------------------------


@router.post(
    "/admin/pages",
    response_model=PageDetailSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def create_page(
    payload: PageCreateRequest,
    repo: SQLAlchemyPageRepository = Depends(_repo),
) -> PageDetailSchema:
    """Créer une page statique (admin)."""
    uc = CreatePageUseCase(repo)
    try:
        element = await uc.execute(
            titre=payload.titre,
            identifiant_url=payload.identifiant_url,
            contenu=payload.contenu,
            titre_meta=payload.titre_meta,
            meta_description=payload.meta_description,
            est_publie=payload.est_publie,
        )
    except PageSlugAlreadyExistsError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return PageDetailSchema.model_validate(element)


@router.put(
    "/admin/pages/{page_id}",
    response_model=PageDetailSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def update_page(
    page_id: int,
    payload: PageUpdateRequest,
    repo: SQLAlchemyPageRepository = Depends(_repo),
) -> PageDetailSchema:
    """Modifier une page statique (admin)."""
    uc = UpdatePageUseCase(repo)
    try:
        element = await uc.execute(
            page_id=page_id,
            titre=payload.titre,
            identifiant_url=payload.identifiant_url,
            contenu=payload.contenu,
            titre_meta=payload.titre_meta,
            meta_description=payload.meta_description,
            est_publie=payload.est_publie,
        )
    except (PageNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PageDetailSchema.model_validate(element)
