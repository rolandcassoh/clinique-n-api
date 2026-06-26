"""Routeur FastAPI du module tag — gestion des étiquettes."""
from fastapi import APIRouter, Depends, HTTPException, Query, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.etiquette.api.schemas import TagCreateSchema, TagSchema, TagUpdateSchema
from app.modules.etiquette.application.cas_utilisation import TagUseCases
from app.modules.etiquette.domain.exceptions import TagNotFoundError, TagSlugConflictError
from app.modules.etiquette.infrastructure.depots import SQLTagRepository

router = APIRouter(tags=["etiquettes"])


def _use_cases(db: AsyncSession = Depends(get_db)) -> TagUseCases:
    return TagUseCases(SQLTagRepository(db))


@router.get("/etiquettes", response_model=list[TagSchema])
async def list_tags(
    type: str | None = Query(default=None),
    search: str | None = Query(default=None),
    uc: TagUseCases = Depends(_use_cases),
) -> list[TagSchema]:
    """Liste toutes les étiquettes avec filtres optionnels."""
    etiquettes = await uc.list_tags(type_filter=type, search=search)
    return [TagSchema.model_validate(t.__dict__) for t in etiquettes]


@router.get("/etiquettes/{tag_id}", response_model=TagSchema)
async def get_tag(tag_id: int, uc: TagUseCases = Depends(_use_cases)) -> TagSchema:
    """Détail d'une étiquette par son id."""
    try:
        etiquette = await uc.get_tag(tag_id)
    except TagNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc))
    return TagSchema.model_validate(etiquette.__dict__)


@router.post("/admin/etiquettes", response_model=TagSchema, status_code=statut.HTTP_201_CREATED)
async def create_tag(
    body: TagCreateSchema,
    uc: TagUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> TagSchema:
    """Créer une étiquette (admin)."""
    try:
        etiquette = await uc.create_tag(nom=body.nom, identifiant_url=body.identifiant_url, type=body.type)
    except TagSlugConflictError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=str(exc))
    return TagSchema.model_validate(etiquette.__dict__)


@router.put("/admin/etiquettes/{tag_id}", response_model=TagSchema)
async def update_tag(
    tag_id: int,
    body: TagUpdateSchema,
    uc: TagUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> TagSchema:
    """Modifier une étiquette (admin)."""
    try:
        etiquette = await uc.update_tag(tag_id, nom=body.nom, identifiant_url=body.identifiant_url, type=body.type)
    except TagNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc))
    except TagSlugConflictError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=str(exc))
    return TagSchema.model_validate(etiquette.__dict__)


@router.delete("/admin/etiquettes/{tag_id}", status_code=statut.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    uc: TagUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> None:
    try:
        await uc.delete_tag(tag_id)
    except TagNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc))
