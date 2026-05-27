"""Router FastAPI du module page (CMS)."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.page.api.schemas import (
    PageCreateRequest,
    PageDetailSchema,
    PageSchema,
    PageUpdateRequest,
)
from app.modules.page.application.use_cases import (
    CreatePageUseCase,
    GetPageBySlugUseCase,
    ListPagesUseCase,
    UpdatePageUseCase,
)
from app.modules.page.domain.exceptions import PageNotFoundError, PageSlugAlreadyExistsError
from app.modules.page.infrastructure.repositories import SQLAlchemyPageRepository
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
    """Liste toutes les pages publiées (sans content)."""
    uc = ListPagesUseCase(repo)
    pages = await uc.execute()
    return [PageSchema.model_validate(p) for p in pages]


@router.get("/pages/{slug}", response_model=PageDetailSchema)
async def get_page(
    slug: str,
    repo: SQLAlchemyPageRepository = Depends(_repo),
) -> PageDetailSchema:
    """Détail d'une page publiée par slug (avec content complet)."""
    uc = GetPageBySlugUseCase(repo)
    try:
        page = await uc.execute(slug)
    except (PageNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PageDetailSchema.model_validate(page)


# ---------------------------------------------------------------------------
# Endpoints admin
# ---------------------------------------------------------------------------


@router.post(
    "/admin/pages",
    response_model=PageDetailSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def create_page(
    payload: PageCreateRequest,
    repo: SQLAlchemyPageRepository = Depends(_repo),
) -> PageDetailSchema:
    """Créer une page statique (admin)."""
    uc = CreatePageUseCase(repo)
    try:
        page = await uc.execute(
            title=payload.title,
            slug=payload.slug,
            content=payload.content,
            meta_title=payload.meta_title,
            meta_description=payload.meta_description,
            is_published=payload.is_published,
        )
    except PageSlugAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return PageDetailSchema.model_validate(page)


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
        page = await uc.execute(
            page_id=page_id,
            title=payload.title,
            slug=payload.slug,
            content=payload.content,
            meta_title=payload.meta_title,
            meta_description=payload.meta_description,
            is_published=payload.is_published,
        )
    except (PageNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PageDetailSchema.model_validate(page)
