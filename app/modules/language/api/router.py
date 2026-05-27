from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.language.api.schemas import LanguageCreateSchema, LanguageSchema, LanguageUpdateSchema
from app.modules.language.application.use_cases import LanguageUseCases
from app.modules.language.domain.exceptions import LanguageCodeConflictError, LanguageNotFoundError
from app.modules.language.infrastructure.repositories import SQLLanguageRepository

router = APIRouter(tags=["languages"])


def _use_cases(db: AsyncSession = Depends(get_db)) -> LanguageUseCases:
    return LanguageUseCases(SQLLanguageRepository(db))


def _to_schema(lang) -> LanguageSchema:
    return LanguageSchema.model_validate(lang.__dict__)


@router.get("/languages", response_model=list[LanguageSchema])
async def list_languages(uc: LanguageUseCases = Depends(_use_cases)) -> list[LanguageSchema]:
    languages = await uc.list_active()
    return [_to_schema(lang) for lang in languages]


@router.get("/languages/default", response_model=LanguageSchema)
async def get_default_language(uc: LanguageUseCases = Depends(_use_cases)) -> LanguageSchema:
    try:
        language = await uc.get_default()
    except LanguageNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return _to_schema(language)


@router.post("/admin/languages", response_model=LanguageSchema, status_code=status.HTTP_201_CREATED)
async def create_language(
    body: LanguageCreateSchema,
    uc: LanguageUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> LanguageSchema:
    try:
        language = await uc.create_language(
            name=body.name, code=body.code, native_name=body.native_name,
            flag=body.flag, is_default=body.is_default, is_active=body.is_active,
            direction=body.direction,
        )
    except LanguageCodeConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return _to_schema(language)


@router.put("/admin/languages/{language_id}", response_model=LanguageSchema)
async def update_language(
    language_id: int,
    body: LanguageUpdateSchema,
    uc: LanguageUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> LanguageSchema:
    try:
        language = await uc.update_language(
            language_id, name=body.name, code=body.code, native_name=body.native_name,
            flag=body.flag, is_default=body.is_default, is_active=body.is_active,
            direction=body.direction,
        )
    except LanguageNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except LanguageCodeConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return _to_schema(language)


@router.patch("/admin/languages/{language_id}/set-default", response_model=LanguageSchema)
async def set_default_language(
    language_id: int,
    uc: LanguageUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> LanguageSchema:
    try:
        language = await uc.set_default(language_id)
    except LanguageNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return _to_schema(language)
