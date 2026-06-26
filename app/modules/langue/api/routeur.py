"""Routeur FastAPI du module langue (language)."""
from fastapi import APIRouter, Depends, HTTPException, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.langue.api.schemas import LanguageCreateSchema, LanguageSchema, LanguageUpdateSchema
from app.modules.langue.application.cas_utilisation import LanguageUseCases
from app.modules.langue.domain.exceptions import LanguageCodeConflictError, LanguageNotFoundError
from app.modules.langue.infrastructure.depots import SQLLanguageRepository

router = APIRouter(tags=["langues"])


def _use_cases(db: AsyncSession = Depends(get_db)) -> LanguageUseCases:
    return LanguageUseCases(SQLLanguageRepository(db))


def _to_schema(lang) -> LanguageSchema:
    return LanguageSchema.model_validate(lang.__dict__)


@router.get("/langues", response_model=list[LanguageSchema])
async def list_languages(uc: LanguageUseCases = Depends(_use_cases)) -> list[LanguageSchema]:
    """Liste toutes les langues actives."""
    langues = await uc.list_active()
    return [_to_schema(lang) for lang in langues]


@router.get("/langues/defaut", response_model=LanguageSchema)
async def get_default_language(uc: LanguageUseCases = Depends(_use_cases)) -> LanguageSchema:
    """Retourne la langue par défaut."""
    try:
        langue = await uc.get_default()
    except LanguageNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc))
    return _to_schema(langue)


@router.post("/admin/langues", response_model=LanguageSchema, status_code=statut.HTTP_201_CREATED)
async def create_language(
    body: LanguageCreateSchema,
    uc: LanguageUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> LanguageSchema:
    """Créer une langue (admin)."""
    try:
        langue = await uc.create_language(
            nom=body.nom, code=body.code, nom_natif=body.nom_natif,
            drapeau=body.drapeau, est_defaut=body.est_defaut, est_actif=body.est_actif,
            sens_ecriture=body.sens_ecriture,
        )
    except LanguageCodeConflictError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=str(exc))
    return _to_schema(langue)


@router.put("/admin/langues/{language_id}", response_model=LanguageSchema)
async def update_language(
    language_id: int,
    body: LanguageUpdateSchema,
    uc: LanguageUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> LanguageSchema:
    """Modifier une langue (admin)."""
    try:
        langue = await uc.update_language(
            language_id, nom=body.nom, code=body.code, nom_natif=body.nom_natif,
            drapeau=body.drapeau, est_defaut=body.est_defaut, est_actif=body.est_actif,
            sens_ecriture=body.sens_ecriture,
        )
    except LanguageNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc))
    except LanguageCodeConflictError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=str(exc))
    return _to_schema(langue)


@router.patch("/admin/langues/{language_id}/definir-defaut", response_model=LanguageSchema)
async def set_default_language(
    language_id: int,
    uc: LanguageUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> LanguageSchema:
    """Définir la langue par défaut (admin)."""
    try:
        langue = await uc.set_default(language_id)
    except LanguageNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc))
    return _to_schema(langue)
